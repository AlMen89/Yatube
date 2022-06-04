from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import POSTS_PER_PAGE

from .forms import PostForm, CommentForm
from .models import Follow, Group, Post, User


def get_page_obj(post_list, page_number):
    """Получает заданную страницу из списка постов"""
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    return paginator.get_page(page_number)


def index(request):
    post_list = Post.objects.all()
    page_number = request.GET.get('page')
    context = {
        'page_obj': get_page_obj(post_list, page_number),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group)
    page_number = request.GET.get('page')
    context = {
        'group': group,
        'page_obj': get_page_obj(post_list, page_number),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=user)
    page_number = request.GET.get('page')
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=user).exists()
    else:
        following = False
    context = {
        'author': user,
        'page_obj': get_page_obj(post_list, page_number),
        'posts_count': post_list.count(),
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posts_count = Post.objects.filter(author=post.author).count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'posts_count': posts_count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:    # проверка разрешения на редактирование
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post = form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follows_set = Follow.objects.filter(user=request.user)
    authors = list(follows_set.values_list('author', flat=True))
    post_list = Post.objects.filter(author__in=authors)
    page_number = request.GET.get('page')
    context = {
        'page_obj': get_page_obj(post_list, page_number),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(
        user=request.user, author=user).exists()
    if user != request.user and not following:
        Follow.objects.create(user=request.user, author=user)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    Follow.objects.get(user=request.user, author=user).delete()
    return redirect('posts:profile', username=username)
