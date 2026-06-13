from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from .forms import CommentForm
from .models import Category, Comment, Post, UserProfile

class TestBlogViews(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="myUsername",
            password="myPassword",
            email="test@test.com"
        )
        UserProfile.objects.update_or_create(
            user=self.user,
            defaults={"is_site_verified": True},
        )
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.post = Post(
            title="Blog title",
            author=self.user,
            slug="blog-title",
            excerpt="Blog excerpt",
            content="Blog content",
            status=1,
            category=self.category,
        )
        self.post.save()

    def test_render_post_detail_page_with_comment_form(self):
        response = self.client.get(reverse(
            'post_detail', args=['blog-title']))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Blog title", response.content)
        self.assertIn(b"Blog content", response.content)
        self.assertIsInstance(
            response.context['comment_form'], CommentForm)

    def test_successful_comment_submission(self):
        """Test for posting a comment on a post"""
        self.client.login(
            username="myUsername", password="myPassword")
        post_data = {
            'body': 'This is a test comment.'
        }
        response = self.client.post(
            reverse('post_detail', args=['blog-title']),
            post_data,
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        comment = Comment.objects.get(post=self.post, author=self.user)
        self.assertIn('This is a test comment.', comment.body)
        self.assertFalse(comment.approved)
        self.assertContains(
            response,
            'نظر شما ثبت شد و در انتظار بررسی است.',
        )
