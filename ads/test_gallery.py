import base64
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.datastructures import MultiValueDict

from ads.cloudinary_cleanup import cloudinary_delivery_url, destroy_cloudinary_asset
from ads.gallery import (
    MAX_GALLERY_IMAGES,
    build_detail_slides,
    get_detail_image_context,
    process_gallery_submission,
    should_show_gallery_lightbox,
    validate_gallery_capacity,
)
from ads.models import Ad, AdGalleryImage
from ads.tests import AdsTestMixin

MINIMAL_JPEG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class AdGalleryTestMixin(AdsTestMixin):
    def _add_gallery_image(self, ad, sort_order=0):
        return AdGalleryImage.objects.create(
            ad=ad,
            image=f"test/ad-gallery-{ad.slug}-{sort_order}",
            sort_order=sort_order,
        )


class AdGalleryVisibilityTests(AdGalleryTestMixin, TestCase):
    def test_free_ad_hides_gallery_on_detail(self):
        ad = self._create_ad("free-gallery", plan="free")
        self._add_gallery_image(ad, sort_order=0)
        self.client.login(username="adowner", password="password123")
        response = self.client.get(reverse("ads:ad_detail", args=[ad.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["ad_show_gallery_lightbox"])
        self.assertNotContains(response, "ad-detail-gallery")

    def test_pro_ad_shows_gallery_lightbox_when_images_exist(self):
        ad = self._create_ad("pro-gallery", plan="pro")
        self._add_gallery_image(ad, sort_order=0)
        self._add_gallery_image(ad, sort_order=1)
        response = self.client.get(reverse("ads:ad_detail", args=[ad.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["ad_show_gallery_lightbox"])
        self.assertContains(response, "ad-detail-gallery")
        self.assertContains(response, "ad-gallery-slides-json")

    def test_pro_ad_without_gallery_uses_single_image(self):
        ad = self._create_ad("pro-single", plan="pro")
        response = self.client.get(reverse("ads:ad_detail", args=[ad.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["ad_show_gallery_lightbox"])

    def test_should_show_gallery_lightbox_is_false_for_free_with_images(self):
        ad = self._create_ad("stored-free", plan="free")
        self._add_gallery_image(ad)
        self.assertFalse(should_show_gallery_lightbox(ad))

    def test_build_detail_slides_puts_primary_first(self):
        ad = self._create_ad("slides-pro", plan="pro")
        self._add_gallery_image(ad, sort_order=0)
        slides = build_detail_slides(ad)
        self.assertEqual(len(slides), 2)
        self.assertTrue(slides[0]["is_primary"])
        self.assertFalse(slides[1]["is_primary"])
        self.assertIn("thumb_url", slides[0])

    def test_plan_transitions_preserve_gallery_images(self):
        ad = self._create_ad("plan-cycle", plan="free")
        self._add_gallery_image(ad, 0)
        self._add_gallery_image(ad, 1)
        self.assertEqual(ad.gallery_images.count(), 2)
        self.assertFalse(should_show_gallery_lightbox(ad))

        ad.plan = "pro"
        ad.save(update_fields=["plan"])
        ad.refresh_from_db()
        self.assertTrue(should_show_gallery_lightbox(ad))

        ad.plan = "free"
        ad.save(update_fields=["plan"])
        ad.refresh_from_db()
        self.assertEqual(ad.gallery_images.count(), 2)
        self.assertFalse(should_show_gallery_lightbox(ad))

        ad.plan = "pro"
        ad.save(update_fields=["plan"])
        ad.refresh_from_db()
        self.assertTrue(should_show_gallery_lightbox(ad))
        self.assertEqual(ad.gallery_images.count(), 2)


class AdGalleryFormTests(AdGalleryTestMixin, TestCase):
    def _image_file(self, name="gallery.png"):
        return SimpleUploadedFile(
            name,
            MINIMAL_JPEG,
            content_type="image/png",
        )

    def test_process_gallery_submission_stores_images_for_free_ad(self):
        ad = self._create_ad("free-store", plan="free")
        files = MultiValueDict({"gallery_images": [self._image_file("g1.png"), self._image_file("g2.png")]})
        with patch("ads.models.AdGalleryImage.objects.create") as mock_create:
            errors = process_gallery_submission(ad, {}, files)
        self.assertEqual(errors, [])
        self.assertEqual(mock_create.call_count, 2)
        self.assertFalse(should_show_gallery_lightbox(ad))

    def test_process_gallery_submission_enforces_max_limit(self):
        ad = self._create_ad("max-gallery", plan="free")
        for index in range(MAX_GALLERY_IMAGES):
            AdGalleryImage.objects.create(
                ad=ad,
                image=f"test/existing-{index}",
                sort_order=index,
            )
        errors = process_gallery_submission(
            ad,
            {},
            {"gallery_images": [self._image_file("one.jpg")]},
        )
        self.assertTrue(errors)
        self.assertEqual(ad.gallery_images.count(), MAX_GALLERY_IMAGES)

    @patch("cloudinary.uploader.upload")
    def test_create_ad_view_accepts_multiple_gallery_files(self, mock_upload):
        mock_upload.side_effect = lambda file, **kwargs: {
            "public_id": f"test/{getattr(file, 'name', 'upload')}",
            "resource_type": "image",
            "version": 1,
            "type": "upload",
            "format": "png",
        }
        self.client.login(username="adowner", password="password123")
        response = self.client.post(
            reverse("ads:create_ad"),
            {
                "title": "Multi gallery upload",
                "category": self.category.pk,
                "target_url": "https://example.com",
                "city": "Tehran",
                "address": "Test address",
                "image": self._image_file("primary.png"),
                "gallery_images": [
                    self._image_file("gallery-1.png"),
                    self._image_file("gallery-2.png"),
                    self._image_file("gallery-3.png"),
                ],
            },
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        ad = Ad.objects.get(title="Multi gallery upload")
        self.assertEqual(ad.gallery_images.count(), 3)
        self.assertGreaterEqual(mock_upload.call_count, 4)

    def test_create_ad_form_allows_multiple_gallery_selection(self):
        self.client.login(username="adowner", password="password123")
        response = self.client.get(reverse("ads:create_ad"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="gallery-images-input"')
        self.assertContains(response, "multiple")
        self.assertContains(response, "ad-gallery-count")
        self.assertContains(response, "ad-gallery-validation")

    def test_csp_allows_blob_urls_for_gallery_previews(self):
        from django.conf import settings

        self.assertIn("blob:", settings.CSP_IMG_SRC)
        self.client.login(username="adowner", password="password123")
        csp = self.client.get(reverse("ads:create_ad")).headers.get(
            "Content-Security-Policy", ""
        )
        self.assertIn("blob:", csp)

    def test_model_save_enforces_max_limit_server_side(self):
        ad = self._create_ad("model-max", plan="free")
        for index in range(MAX_GALLERY_IMAGES):
            AdGalleryImage.objects.create(
                ad=ad,
                image=f"test/model-{index}",
                sort_order=index,
            )
        with self.assertRaises(ValidationError):
            validate_gallery_capacity(ad, additional_images=1)

    def test_get_detail_image_context_matches_visibility_rules(self):
        ad = self._create_ad("context-pro", plan="pro")
        AdGalleryImage.objects.create(ad=ad, image="test/gallery-1", sort_order=0)
        context = get_detail_image_context(ad)
        self.assertTrue(context["ad_show_gallery_lightbox"])
        self.assertEqual(len(context["ad_gallery_slides"]), 2)
        self.assertIn("detail_primary_image_url", context)


class AdGalleryPerformanceAndCleanupTests(AdGalleryTestMixin, TestCase):
    def _prefetched_ad(self, ad):
        return (
            Ad.objects.select_related("category", "owner")
            .prefetch_related("gallery_images")
            .get(pk=ad.pk)
        )

    def test_get_detail_image_context_avoids_n_plus_one_when_prefetched(self):
        ad = self._create_ad("query-pro", plan="pro")
        self._add_gallery_image(ad, 0)
        ad_one = self._prefetched_ad(ad)

        with CaptureQueriesContext(connection) as one_image_queries:
            context_one = get_detail_image_context(ad_one)
        self.assertEqual(len(context_one["ad_gallery_slides"]), 2)

        for index in range(1, 8):
            self._add_gallery_image(ad, index)
        ad_many = self._prefetched_ad(ad)

        with CaptureQueriesContext(connection) as many_image_queries:
            context_many = get_detail_image_context(ad_many)
        self.assertEqual(len(context_many["ad_gallery_slides"]), 9)
        self.assertEqual(
            len(one_image_queries.captured_queries),
            len(many_image_queries.captured_queries),
        )
        self.assertEqual(len(one_image_queries.captured_queries), 0)

    @patch("cloudinary.uploader.destroy")
    def test_deleting_gallery_image_destroys_cloudinary_asset(self, mock_destroy):
        ad = self._create_ad("delete-gallery", plan="pro")
        gallery_image = self._add_gallery_image(ad)
        gallery_image.delete()
        mock_destroy.assert_called_once()

    @patch("cloudinary.uploader.destroy")
    def test_deleting_ad_destroys_primary_image_asset(self, mock_destroy):
        ad = self._create_ad("delete-ad", plan="pro", image="test/primary-image")
        self._add_gallery_image(ad)
        ad_id = ad.pk
        ad.delete()
        self.assertFalse(Ad.objects.filter(pk=ad_id).exists())
        self.assertGreaterEqual(mock_destroy.call_count, 2)

    def test_delivery_url_uses_auto_format_and_quality(self):
        url = cloudinary_delivery_url("test/sample-image", width=800, crop="limit")
        self.assertIn("f_auto", url)
        self.assertIn("q_auto", url)

    def test_delivery_url_falls_back_when_cloudinary_is_unconfigured(self):
        with patch("cloudinary.utils.cloudinary_url", side_effect=ValueError("no cloud_name")):
            url = cloudinary_delivery_url("test/sample-image", width=800)
        self.assertEqual(url, "test/sample-image")

    @patch("cloudinary.uploader.destroy")
    def test_destroy_cloudinary_asset_handles_public_id_strings(self, mock_destroy):
        destroy_cloudinary_asset("test/sample-image")
        mock_destroy.assert_called_once_with("test/sample-image")
