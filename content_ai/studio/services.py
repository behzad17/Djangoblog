"""AI Studio service — compose existing AI layers (APF-002)."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from content_ai.config import (
    DEFAULT_PROMPT_VERSION,
    DEFAULT_STYLE,
    FEATURE_FLAGS,
    SUPPORTED_PROMPT_VERSIONS,
    SUPPORTED_STYLES,
    SYSTEM_MODULE_ORDER,
)
from content_ai.evaluation import ComparisonEngine, Evaluator, create_snapshot
from content_ai.knowledge import (
    KnowledgeInjector,
    load_manifest,
    parse_knowledge_modules,
)
from content_ai.knowledge.utils import DEFAULT_KNOWLEDGE_ROOT, MANIFEST_FILENAME
from content_ai.prompts.builders import PromptBuilder
from content_ai.providers import get_provider, list_providers
from content_ai.studio.session import GenerationRecord, StudioSession, utc_now
from content_ai.workflow import (
    ALLOWED_TRANSITIONS,
    WorkflowOrchestrator,
    WorkflowState,
    can_transition,
    create_initial_context,
)


class StudioService:
    """
    Orchestrates AI Studio labs by composing existing packages.

    Does not modify production prompts/knowledge.
    Does not publish content.
    """

    def __init__(
        self,
        prompt_builder: PromptBuilder | None = None,
        evaluator: Evaluator | None = None,
        workflow: WorkflowOrchestrator | None = None,
        injector: KnowledgeInjector | None = None,
    ):
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.evaluator = evaluator or Evaluator()
        self.workflow = workflow or WorkflowOrchestrator()
        self.injector = injector or KnowledgeInjector()
        self.comparison_engine = ComparisonEngine()

    def new_session(self, *, environment: str = 'testing') -> StudioSession:
        session = StudioSession()
        session.set_environment(environment)
        return session

    # --- Prompt Lab (RFC-001) ---

    def list_prompt_options(self) -> dict:
        return {
            'versions': list(SUPPORTED_PROMPT_VERSIONS),
            'styles': list(SUPPORTED_STYLES),
            'default_version': DEFAULT_PROMPT_VERSION,
            'default_style': DEFAULT_STYLE,
            'system_module_order': list(SYSTEM_MODULE_ORDER),
            'note': 'Studio previews only — production prompts are not modified.',
        }

    def preview_prompt(
        self,
        session: StudioSession,
        *,
        version: str = DEFAULT_PROMPT_VERSION,
        style: str = DEFAULT_STYLE,
        user_prompt: str = '',
    ) -> dict:
        assembled = self.prompt_builder.build(
            version=version,
            style=style,
            user_prompt=user_prompt,
        )
        components = self._prompt_components(version, style, user_prompt)
        estimated_tokens = max(1, len(assembled) // 4)
        payload = {
            'version': version,
            'style': style,
            'assembled_prompt': assembled,
            'components': components,
            'estimated_token_usage': estimated_tokens,
            'environment': session.environment,
        }
        session.metadata['last_prompt_preview'] = {
            'version': version,
            'style': style,
            'estimated_token_usage': estimated_tokens,
        }
        session.last_explanations = [
            f'Prompt assembled with PromptBuilder version={version} style={style}.',
            'This preview does not change production prompt files.',
        ]
        session.touch()
        return payload

    def _prompt_components(
        self,
        version: str,
        style: str,
        user_prompt: str,
    ) -> dict[str, str]:
        validator = self.prompt_builder.validator
        return {
            'identity': validator.system_path(version, 'identity').read_text(
                encoding='utf-8'
            ),
            'audience': validator.system_path(version, 'audience').read_text(
                encoding='utf-8'
            ),
            'writing': validator.system_path(version, 'writing').read_text(
                encoding='utf-8'
            ),
            'style': validator.style_path(version, style).read_text(
                encoding='utf-8'
            ),
            'output_schema': validator.system_path(
                version, 'output_schema'
            ).read_text(encoding='utf-8'),
            'user_prompt': (user_prompt or '').strip() or '(empty)',
        }

    def compare_prompts(
        self,
        session: StudioSession,
        *,
        version_a: str,
        style_a: str,
        version_b: str,
        style_b: str,
        user_prompt: str = '',
    ) -> dict:
        left = self.preview_prompt(
            session, version=version_a, style=style_a, user_prompt=user_prompt
        )
        right = self.preview_prompt(
            session, version=version_b, style=style_b, user_prompt=user_prompt
        )
        result = {
            'dimension': 'prompt',
            'a': left,
            'b': right,
            'automatic_winner': None,
            'note': 'Editors decide — no automatic winner selection.',
        }
        session.last_comparison = {
            'dimension': 'prompt',
            'a_label': f'{version_a}/{style_a}',
            'b_label': f'{version_b}/{style_b}',
        }
        session.last_explanations = [
            'Side-by-side prompt comparison prepared.',
            'No automatic winner — editorial judgment required.',
        ]
        session.touch()
        return result

    # --- Knowledge Lab (RFC-002) ---

    def browse_knowledge(self, session: StudioSession) -> dict:
        root = Path(DEFAULT_KNOWLEDGE_ROOT)
        manifest_path = root / MANIFEST_FILENAME
        raw = load_manifest(manifest_path) if manifest_path.exists() else {}
        modules = parse_knowledge_modules(knowledge_root=root)
        meta = (raw or {}).get('_meta') or {}
        packs = [
            {
                'name': m.name,
                'title': m.title,
                'file': m.file,
                'tags': list(m.tags),
                'priority': m.priority,
                'content_chars': len(m.content or ''),
                'metadata': dict(m.metadata),
            }
            for m in modules
        ]
        payload = {
            'knowledge_version': meta.get('version') or 'manifest',
            'module_count': len(packs),
            'packs': packs,
            'injection_preview': self.injector.inject(
                '[[USER_PROMPT]]', modules[:3] if modules else []
            ),
            'rag_ready': False,
            'note': 'Retrieval not implemented — browse/preview only.',
        }
        session.metadata['knowledge'] = {
            'knowledge_version': payload['knowledge_version'],
            'module_count': payload['module_count'],
        }
        session.last_explanations = [
            f'Loaded {len(packs)} knowledge modules from manifest.',
            'Knowledge Lab does not modify production knowledge files.',
        ]
        session.touch()
        return payload

    def compare_knowledge(
        self,
        session: StudioSession,
        *,
        pack_a: str = '',
        pack_b: str = '',
    ) -> dict:
        modules = parse_knowledge_modules()
        by_name = {m.name: m for m in modules}

        def _pack(name: str) -> dict:
            mod = by_name.get(name)
            if mod is None:
                return {'name': name, 'found': False}
            return {
                'name': mod.name,
                'found': True,
                'title': mod.title,
                'tags': list(mod.tags),
                'priority': mod.priority,
                'metadata': dict(mod.metadata),
                'content_preview': (mod.content or '')[:800],
            }

        # Default to first two packs when names omitted.
        names = list(by_name.keys())
        a_name = pack_a or (names[0] if names else '')
        b_name = pack_b or (names[1] if len(names) > 1 else a_name)
        result = {
            'dimension': 'knowledge',
            'a': _pack(a_name),
            'b': _pack(b_name),
            'automatic_winner': None,
            'note': 'Editors decide — no automatic winner selection.',
        }
        session.last_comparison = {
            'dimension': 'knowledge',
            'a_label': a_name,
            'b_label': b_name,
        }
        session.touch()
        return result

    # --- Provider Lab (RFC-005) ---

    def inspect_providers(self, session: StudioSession) -> dict:
        providers = []
        for name in list_providers():
            try:
                provider = get_provider(name)
            except Exception as exc:  # noqa: BLE001 — surface inspect errors
                providers.append({
                    'name': name,
                    'status': 'error',
                    'error': str(exc),
                    'health_check': False,
                })
                continue
            caps = provider.capabilities()
            models = []
            for model in provider.discover_models() or []:
                models.append({
                    'provider': model.provider,
                    'model': model.model,
                    'context_window': model.context_window,
                    'supports_json': model.supports_json,
                    'supports_streaming': model.supports_streaming,
                    'status': model.status,
                })
            providers.append({
                'name': name,
                'status': 'available',
                'health_check': bool(provider.health_check()),
                'capabilities': asdict(caps),
                'models': models,
                'estimated_cost': None,
                'latency': None,
                'note': 'Cost/latency are placeholders until live probes.',
            })
        payload = {
            'providers': providers,
            'environment': session.environment,
        }
        session.metadata['providers'] = {
            'count': len(providers),
            'names': [p['name'] for p in providers],
        }
        session.last_explanations = [
            'Provider Lab reused RFC-005 registry / capabilities.',
            'Health checks are adapter placeholders.',
        ]
        session.touch()
        return payload

    # --- Evaluation Lab (RFC-004) ---

    def evaluate_text(
        self,
        session: StudioSession,
        *,
        output_text: str,
        input_text: str = '',
        prompt_version: str = '',
        knowledge_version: str = '',
        provider: str = 'studio',
        workflow_stage: str = 'studio',
    ) -> dict:
        snap = create_snapshot(
            output_text=output_text or '',
            input_text=input_text or '',
            language='fa',
            workflow_stage=workflow_stage or 'studio',
            prompt_version=prompt_version or '',
            knowledge_version=knowledge_version or '',
            provider=provider or 'studio',
        )
        result = self.evaluator.evaluate(snap)
        payload = {
            'overall': result.aggregate.overall_score,
            'weighted': result.aggregate.weighted_score,
            'confidence': result.aggregate.confidence_score,
            'scores': dict(result.snapshot.scores),
            'warnings': list(result.aggregate.warnings),
            'prompt_version': snap.prompt_version,
            'knowledge_version': snap.knowledge_version,
            'provider': snap.provider,
            'latency_ms': snap.latency_ms,
            'estimated_cost': snap.estimated_cost,
        }
        session.metadata['last_evaluation'] = payload
        session.last_explanations = [
            'Evaluation used RFC-004 Evaluator heuristics.',
            f'Overall score: {payload["overall"]}',
        ]
        session.touch()
        return payload

    # --- Workflow Inspector (RFC-003) ---

    def inspect_workflow(
        self,
        session: StudioSession,
        *,
        state: str = 'idea',
        title: str = 'Studio inspection',
    ) -> dict:
        try:
            current = WorkflowState(state)
        except ValueError as exc:
            raise ValueError(f'Unknown workflow state: {state!r}') from exc
        ctx = create_initial_context(title=title or 'Studio inspection')
        ctx.state = current
        transitions = {
            src.value: sorted(t.value for t in targets)
            for src, targets in ALLOWED_TRANSITIONS.items()
        }
        payload = {
            'current_stage': current.value,
            'context': {
                'title': title,
                'state': current.value,
                'language': ctx.language,
                'warnings': list(ctx.warnings),
                'errors': list(ctx.errors),
            },
            'allowed_from_current': sorted(
                t.value for t in (ALLOWED_TRANSITIONS.get(current) or [])
            ),
            'can_examples': {
                'to_drafting': can_transition(current, WorkflowState.DRAFTING),
                'to_published': can_transition(current, WorkflowState.PUBLISHED),
            },
            'transitions_map': transitions,
            'stages': list(self.workflow.list_stages()),
            'execution_log': [],
            'future_stage_hooks': [
                'on_enter_stage',
                'on_exit_stage',
                'on_transition',
            ],
            'note': 'Inspector is read-only — does not run production workflow.',
        }
        session.metadata['workflow'] = {
            'current_stage': current.value,
        }
        session.last_explanations = [
            f'Workflow Inspector showing state={current.value}.',
            'Studio never auto-publishes or advances production workflows.',
        ]
        session.touch()
        return payload

    # --- Test generation + history ---

    def run_test_generation(
        self,
        session: StudioSession,
        *,
        user_prompt: str = '',
        version: str = DEFAULT_PROMPT_VERSION,
        style: str = DEFAULT_STYLE,
        provider_name: str = 'mock',
        knowledge_version: str = '',
        workflow_stage: str = 'studio',
    ) -> dict:
        assembled = self.prompt_builder.build(
            version=version,
            style=style,
            user_prompt=user_prompt,
        )
        provider = get_provider(provider_name or 'mock')
        result = provider.generate(assembled, task='post_generation')
        output = '' if result.content is None else str(result.content)
        telemetry = result.telemetry
        latency = telemetry.duration_ms if telemetry else None
        token_usage = telemetry.token_usage if telemetry else None
        estimated_cost = telemetry.estimated_cost if telemetry else None
        model = (telemetry.model if telemetry else '') or ''

        evaluation = self.evaluate_text(
            session,
            output_text=output,
            input_text=user_prompt,
            prompt_version=version,
            knowledge_version=knowledge_version,
            provider=provider_name or 'mock',
            workflow_stage=workflow_stage,
        )
        warnings = list(result.warnings or [])
        warnings.append('Studio test generation — not saved to Blog.')
        record = GenerationRecord(
            generation_id=str(uuid4()),
            timestamp=utc_now(),
            prompt_version=version,
            knowledge_version=knowledge_version or '',
            provider=provider_name or 'mock',
            model=model,
            workflow_stage=workflow_stage or 'studio',
            input_text=user_prompt or '',
            output_text=output,
            assembled_prompt=assembled,
            evaluation_score=evaluation.get('overall'),
            evaluation=evaluation,
            latency_ms=latency,
            token_usage=dict(token_usage) if token_usage else None,
            estimated_cost=estimated_cost,
            warnings=warnings,
            explainability={
                'prompt_version': version,
                'style': style,
                'knowledge_version': knowledge_version or '',
                'workflow_stage': workflow_stage or 'studio',
                'source_summary': (user_prompt or '')[:240],
                'evaluation_summary': {
                    'overall': evaluation.get('overall'),
                    'warnings': evaluation.get('warnings'),
                },
                'ai_reasoning_metadata': None,
                'environment': session.environment,
            },
            environment=session.environment,
        )
        session.push_generation(record)
        session.last_explanations = [
            'Test generation completed in Studio environment.',
            'Result is session-local history only — production untouched.',
        ]
        return record.to_dict()

    def generation_history(self, session: StudioSession) -> dict:
        return {
            'count': len(session.history),
            'items': [item.to_dict() for item in session.history],
            'note': 'Local session history — durable persistence is future work.',
        }

    def compare_generations(
        self,
        session: StudioSession,
        *,
        generation_id_a: str,
        generation_id_b: str,
    ) -> dict:
        a = session.get_generation(generation_id_a)
        b = session.get_generation(generation_id_b)
        if a is None or b is None:
            raise ValueError('Both generation IDs must exist in Studio history.')
        result = {
            'dimension': 'generation',
            'a': a.to_dict(),
            'b': b.to_dict(),
            'prompt': {
                'a': a.prompt_version,
                'b': b.prompt_version,
            },
            'knowledge': {
                'a': a.knowledge_version,
                'b': b.knowledge_version,
            },
            'provider': {
                'a': a.provider,
                'b': b.provider,
            },
            'output': {
                'a': a.output_text,
                'b': b.output_text,
            },
            'evaluation': {
                'a': a.evaluation,
                'b': b.evaluation,
            },
            'automatic_winner': None,
            'note': 'Editors decide — no automatic winner selection.',
        }
        session.last_comparison = {
            'dimension': 'generation',
            'a_label': a.generation_id,
            'b_label': b.generation_id,
        }
        session.last_explanations = [
            'Side-by-side generation comparison prepared.',
            'No automatic winner selection.',
        ]
        session.touch()
        return result

    # --- System Health ---

    def system_health(self, session: StudioSession) -> dict:
        payload = {
            'environment': session.environment,
            'writes_production': False,
            'auto_publish_allowed': False,
            'feature_flags': dict(FEATURE_FLAGS),
            'providers_registered': list_providers(),
            'prompt_versions': list(SUPPORTED_PROMPT_VERSIONS),
            'linked_features': {
                'editorial_workspace': '/content-ai/workspace/',
                'sandbox': '/content-ai/sandbox/',
            },
            'health_placeholders': {
                'prompt_engine': 'architecture',
                'knowledge_engine': 'passive',
                'provider_platform': 'compatible',
                'evaluation': 'passive',
                'workflow': 'inactive',
            },
            'note': (
                'Studio distinguishes testing/experimental from production. '
                'Experiments never overwrite production automatically.'
            ),
        }
        session.metadata['system_health'] = {
            'environment': session.environment,
            'flag_count': len(FEATURE_FLAGS),
        }
        session.last_explanations = [
            f'Studio environment={session.environment}.',
            'Production prompts and knowledge remain read-only from Studio.',
        ]
        session.touch()
        return payload
