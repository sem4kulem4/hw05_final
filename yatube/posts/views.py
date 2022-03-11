from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


NUMBER_OF_POSTS = 10


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_posts = group.posts.all()
    paginator = Paginator(group_posts, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    content = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', content)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user_posts = author.posts.all()
    paginator = Paginator(user_posts, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if request.user.is_anonymous or request.user == author:
        context = {
            'page_obj': page_obj,
            'author': author,
            'not_show_button': True
        }
        return render(request, 'posts/profile.html', context)
    if Follow.objects.filter(user=request.user, author=author).exists():
        following = True
    else:
        following = False
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
        'not_show_button': False
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post__id=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None, )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(
        request,
        'posts/create_post.html',
        {'form': form, 'is_edit': is_edit, 'post_id': post_id}
    )


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    following_authors = Follow.objects.filter(user=request.user).values_list('author_id', flat=True)
    following_posts = Post.objects.filter(author_id__in=following_authors)
    paginator = Paginator(following_posts, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'title': 'Ваши подписки',
        'following': True
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follower = request.user
    author = User.objects.get(username=username)
    if Follow.objects.filter(user=follower, author=author).exists():
        return render(request, 'posts/index.html')
    if follower == author:
        return render(request, 'posts/index.html')
    Follow.objects.create(user=follower, author=author)
    return render(request, 'posts/follow.html')


@login_required
def profile_unfollow(request, username):
    follower = request.user
    author = User.objects.get(username=username)
    Follow.objects.filter(user=follower, author=author).delete()
    return render(request, 'posts/follow.html')
