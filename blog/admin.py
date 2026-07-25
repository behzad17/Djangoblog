from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from content_ai.admin_editorial import (
    SESSION_SUGGESTION_KEY,
    AdminGenerateWithAIForm,
    apply_suggestion_to_initial,
    suggestion_from_draft,
)
from content_ai.editorial.service import EditorialAIService
from content_ai.providers.exceptions import (
    GenerationError,
    ProviderConfigurationError,
    ProviderNotFound,
)

from .models import Post, Comment, Category, UserProfile, PostViewCount

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    list_display = ('display_order', 'name', 'slug', 'post_count', 'created_on')
    list_display_links = ('name',)
    list_editable = ('display_order',)
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']
    
    def post_count(self, obj):
        """Returns the number of published posts in this category."""
        return obj.posts.filter(status=1, is_deleted=False).count()
    post_count.short_description = 'Published Posts'


class ExpertAuthorFilter(SimpleListFilter):
    """Custom filter for posts by expert authors."""
    title = 'Expert Author'
    parameter_name = 'expert_author'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Yes'),
            ('0', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            # Filter for expert authors - only users with profiles that have can_publish_without_approval=True
            return queryset.filter(
                author__profile__isnull=False,
                author__profile__can_publish_without_approval=True
            ).select_related('author', 'author__profile')
        elif self.value() == '0':
            # Filter for non-expert authors - users without profiles or with can_publish_without_approval=False
            return queryset.filter(
                Q(author__profile__isnull=True) | 
                Q(author__profile__can_publish_without_approval=False)
            ).select_related('author', 'author__profile')
        return queryset


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin interface for Post model with plain textareas (no Summernote)."""

    change_form_template = 'admin/blog/post/change_form.html'
    list_display = ('title', 'slug', 'category', 'status', 'pinned', 'pinned_row', 'url_status', 'is_deleted', 'deleted_status', 'created_on')
    search_fields = ['title', 'content', 'external_url']
    list_filter = ('status', 'category', 'pinned', 'url_approved', 'is_deleted', 'created_on', ExpertAuthorFilter,)
    # Slug is auto-generated from title in Post.save() method
    # prepopulated_fields removed - slug will be generated automatically for Persian titles
    # Using plain textareas instead of Summernote for admin panel
    fieldsets = (
        ('Post Information', {
            'fields': ('title', 'slug', 'author', 'category', 'status', 'pinned', 'pinned_row')
        }),
        ('Content', {
            'fields': ('content', 'excerpt', 'featured_image', 'extra_image_1', 'extra_image_2'),
            'description': 'Main post content (required). Excerpt is optional summary.'
        }),
        ('Event Details', {
            'fields': ('event_start_date', 'event_end_date', 'event_location'),
            'description': 'Use these fields for posts in the Events category (رویدادها).',
            'classes': ('collapse',),
        }),
        ('External URL', {
            'fields': ('external_url', 'url_approved'),
            'description': 'Users can add an external URL. Admin must approve it before it will be displayed.'
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at', 'deleted_by'),
            'description': 'Soft delete information. Deleted posts are hidden from public views.',
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_on', 'updated_on', 'deleted_at', 'deleted_by', 'slug')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'generate-with-ai/',
                self.admin_site.admin_view(self.generate_with_ai_view),
                name='blog_post_generate_with_ai',
            ),
        ]
        return custom_urls + urls

    def _can_show_generate_with_ai(self, request, obj=None):
        """Button only for add or Draft edits; never for published posts."""
        if obj is None:
            return self.has_add_permission(request)
        return (
            self.has_change_permission(request, obj)
            and obj.status == 0
            and not obj.is_deleted
        )

    def _generate_with_ai_url(self, obj=None):
        url = reverse('admin:blog_post_generate_with_ai')
        if obj is not None:
            return f'{url}?post_id={obj.pk}'
        return url

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        obj = None
        if object_id:
            obj = self.get_object(request, object_id)

        if request.method == 'GET':
            suggestion = request.session.pop(SESSION_SUGGESTION_KEY, None)
            if suggestion:
                request._content_ai_suggestion = suggestion
                messages.info(
                    request,
                    'AI suggestion loaded into the form. Review and save as '
                    'Draft when ready. Nothing was saved automatically.',
                )

        show = self._can_show_generate_with_ai(request, obj)
        extra_context['show_generate_with_ai'] = show
        extra_context['generate_with_ai_url'] = (
            self._generate_with_ai_url(obj) if show else ''
        )
        return super().changeform_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )

    def get_form(self, request, obj=None, change=False, **kwargs):
        Form = super().get_form(request, obj, change=change, **kwargs)
        suggestion = getattr(request, '_content_ai_suggestion', None)
        if not suggestion:
            return Form

        class AISuggestedPostForm(Form):
            def __init__(self, *args, _suggestion=suggestion, **form_kwargs):
                initial = apply_suggestion_to_initial(
                    form_kwargs.get('initial') or {},
                    _suggestion,
                )
                form_kwargs['initial'] = initial
                super().__init__(*args, **form_kwargs)

        AISuggestedPostForm.__name__ = Form.__name__
        AISuggestedPostForm.__qualname__ = getattr(
            Form,
            '__qualname__',
            Form.__name__,
        )
        return AISuggestedPostForm

    def generate_with_ai_view(self, request):
        """
        Intermediate Admin page: collect prompts, generate suggestion, return
        to the change form. Never persists or publishes.
        """
        post = None
        post_id = request.GET.get('post_id') or request.POST.get('post_id')
        if post_id:
            post = self.get_object(request, post_id)
            if post is None:
                messages.error(request, 'Post not found.')
                return redirect('admin:blog_post_changelist')
            if post.status != 0 or post.is_deleted:
                messages.error(
                    request,
                    'Generate with AI is only available for Draft posts.',
                )
                return redirect('admin:blog_post_change', post.pk)
            if not self.has_change_permission(request, post):
                raise PermissionDenied
            cancel_url = reverse('admin:blog_post_change', args=[post.pk])
        else:
            if not self.has_add_permission(request):
                raise PermissionDenied
            cancel_url = reverse('admin:blog_post_add')

        initial = {}
        if post is not None and request.method == 'GET':
            initial = {
                'title': post.title,
                'category': post.category_id,
            }

        form = AdminGenerateWithAIForm(
            request.POST or None,
            initial=initial,
        )
        error = None

        if request.method == 'POST' and form.is_valid():
            cleaned = form.cleaned_data
            category = cleaned['category']
            try:
                draft = EditorialAIService().generate_draft(
                    title=cleaned.get('title') or '',
                    language=cleaned.get('language') or '',
                    category=category.name,
                    context=cleaned.get('context') or '',
                    instructions=cleaned.get('instructions') or '',
                )
            except ProviderNotFound as exc:
                error = str(exc)
            except ProviderConfigurationError as exc:
                error = str(exc)
            except GenerationError as exc:
                error = str(exc)
            except Exception:
                error = 'Unexpected generation failure. Please try again.'
            else:
                suggestion = suggestion_from_draft(
                    draft,
                    category_id=category.pk,
                )
                if not suggestion['title'] and cleaned.get('title'):
                    suggestion['title'] = cleaned['title']
                request.session[SESSION_SUGGESTION_KEY] = suggestion
                request.session.modified = True
                if post is not None:
                    return redirect('admin:blog_post_change', post.pk)
                return redirect('admin:blog_post_add')

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'form': form,
            'post': post,
            'error': error,
            'cancel_url': cancel_url,
            'title': 'Generate with AI',
        }
        return render(
            request,
            'admin/blog/post/generate_with_ai.html',
            context,
        )

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))
        show_extra_images = obj and getattr(obj, 'category', None) and getattr(obj.category, 'slug', None) == 'photo-gallery'
        if not show_extra_images:
            for i, (name, options) in enumerate(fieldsets):
                if name == 'Content':
                    fields_list = [f for f in options['fields'] if f not in ('extra_image_1', 'extra_image_2')]
                    fieldsets[i] = (name, {**options, 'fields': tuple(fields_list)})
                    break
        return fieldsets

    def get_queryset(self, request):
        """Override queryset to handle expert_author filter parameter."""
        qs = super().get_queryset(request)
        # Handle expert_author filter from URL parameter
        if request.GET.get('expert_author') == '1':
            # Filter for expert authors - only users with profiles that have can_publish_without_approval=True
            qs = qs.filter(
                author__profile__isnull=False,
                author__profile__can_publish_without_approval=True
            ).select_related('author', 'author__profile')
        elif request.GET.get('expert_author') == '0':
            # Filter for non-expert authors - users without profiles or with can_publish_without_approval=False
            qs = qs.filter(
                Q(author__profile__isnull=True) | 
                Q(author__profile__can_publish_without_approval=False)
            ).select_related('author', 'author__profile')
        return qs

    def url_status(self, obj):
        """Display URL approval status."""
        if not obj.external_url:
            return "No URL"
        elif obj.url_approved:
            return "✓ Approved"
        else:
            return "⏳ Pending"
    url_status.short_description = 'URL Status'

    def deleted_status(self, obj):
        """Display soft delete status."""
        if obj.is_deleted:
            deleted_info = f"Deleted"
            if obj.deleted_at:
                deleted_info += f" ({obj.deleted_at.strftime('%Y-%m-%d')})"
            if obj.deleted_by:
                deleted_info += f" by {obj.deleted_by.username}"
            return format_html(
                '<span style="color: red; font-weight: bold;">🗑️ {}</span>',
                deleted_info
            )
        return format_html('<span style="color: green;">✓ Active</span>')
    deleted_status.short_description = 'Delete Status'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    list_display = ('user', 'expert_status', 'expert_since', 'site_verified_status', 'post_count')
    list_filter = ('can_publish_without_approval', 'is_site_verified', 'expert_since', 'site_verified_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('expert_since', 'site_verified_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Site Verification', {
            'fields': ('is_site_verified', 'site_verified_at'),
            'description': 'Site verification is required for write actions (posts, comments, ads).'
        }),
        ('Expert Access', {
            'fields': ('can_publish_without_approval', 'expert_since'),
            'description': 'Grant or revoke expert publishing access. Expert users can publish posts without admin approval.'
        }),
    )
    
    def site_verified_status(self, obj):
        """Display site verification status."""
        if obj.is_site_verified:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Verified</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Not Verified</span>'
        )
    site_verified_status.short_description = 'Site Verified'
    
    def expert_status(self, obj):
        """Display expert status with colored badge."""
        if obj.can_publish_without_approval:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Expert</span>'
            )
        return format_html(
            '<span style="color: gray;">Regular User</span>'
        )
    expert_status.short_description = 'Status'
    
    def post_count(self, obj):
        """Display count of published posts by this user."""
        return obj.user.blog_posts.filter(status=1, is_deleted=False).count()
    post_count.short_description = 'Published Posts'
    
    def save_model(self, request, obj, form, change):
        """Set expert_since when access is granted for the first time."""
        if obj.can_publish_without_approval and not obj.expert_since:
            from django.utils import timezone
            obj.expert_since = timezone.now()
        elif not obj.can_publish_without_approval:
            obj.expert_since = None
        super().save_model(request, obj, form, change)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for comment moderation."""
    
    list_display = (
        'id',
        'body_preview',
        'author',
        'post',
        'approved',  # Must be in list_display to use in list_editable
        'approval_status',
        'moderation_reason_display',
        'created_on',
        'reviewed_info'
    )
    
    list_filter = (
        'approved',
        'moderation_reason',
        'created_on',
        'reviewed_at',
    )
    
    search_fields = ('body', 'author__username', 'post__title')
    
    list_editable = ('approved',)  # Quick approve/reject
    
    readonly_fields = ('created_on', 'reviewed_by', 'reviewed_at')
    
    actions = ['approve_comments', 'reject_comments']
    
    fieldsets = (
        ('Comment Content', {
            'fields': ('body', 'post', 'author')
        }),
        ('Moderation', {
            'fields': (
                'approved',
                'moderation_reason',
                'reviewed_by',
                'reviewed_at'
            )
        }),
        ('Timestamps', {
            'fields': ('created_on',),
            'classes': ('collapse',)
        }),
    )
    
    def body_preview(self, obj):
        """Show first 50 characters of comment."""
        if len(obj.body) > 50:
            return obj.body[:50] + '...'
        return obj.body
    body_preview.short_description = 'Comment'
    
    def approval_status(self, obj):
        """Color-coded approval status."""
        if obj.approved:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Approved</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">⏳ Pending</span>'
        )
    approval_status.short_description = 'Status'
    
    def moderation_reason_display(self, obj):
        """Display moderation reason with icon."""
        if not obj.moderation_reason:
            return '-'
        reasons = {
            'new_user': '👤 New User',
            'contains_link': '🔗 Contains Link',
            'manual_review': '📋 Manual Review',
        }
        return reasons.get(obj.moderation_reason, obj.moderation_reason)
    moderation_reason_display.short_description = 'Reason'
    
    def reviewed_info(self, obj):
        """Show who reviewed and when."""
        if obj.reviewed_by and obj.reviewed_at:
            return f"{obj.reviewed_by.username} ({obj.reviewed_at.strftime('%Y-%m-%d %H:%M')})"
        return '-'
    reviewed_info.short_description = 'Reviewed By'
    
    def approve_comments(self, request, queryset):
        """Bulk approve action."""
        from django.utils import timezone
        updated = queryset.update(
            approved=True,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} comment(s) approved.")
    approve_comments.short_description = 'Approve selected comments'
    
    def reject_comments(self, request, queryset):
        """Bulk reject action."""
        from django.utils import timezone
        updated = queryset.update(
            approved=False,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} comment(s) rejected.")
    reject_comments.short_description = 'Reject selected comments'
    
    def save_model(self, request, obj, form, change):
        """Track who reviewed the comment."""
        from django.utils import timezone
        if change and 'approved' in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


# PageView model removed from admin to keep admin fast
# (model still exists in database, just not registered in admin)

@admin.register(PostViewCount)
class PostViewCountAdmin(admin.ModelAdmin):
    """Admin interface for PostViewCount model."""
    list_display = ('post_title', 'total_views', 'last_viewed_at', 'updated_at')
    search_fields = []  # Removed post__title to prevent 500 errors with orphaned records
    list_filter = ('updated_at',)  # Only filter on non-nullable field
    readonly_fields = ('updated_at',)
    ordering = ['-total_views']
    
    def get_queryset(self, request):
        """Optimize queryset and filter out orphaned records."""
        qs = super().get_queryset(request)
        return qs.select_related('post').filter(post__isnull=False)
    
    def post_title(self, obj):
        """Safely display post title."""
        if obj.post:
            return obj.post.title
        return '(Post deleted)'
    post_title.short_description = 'Post'
    
    fieldsets = (
        ('Post', {
            'fields': ('post',)
        }),
        ('View Statistics', {
            'fields': ('total_views', 'last_viewed_at', 'updated_at'),
            'description': 'Aggregated view counts. Updated automatically when views are tracked.'
        }),
    )
