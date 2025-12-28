from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth import get_user_model
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, CreationForm, EditUserForm

User = get_user_model()


def index(request):
    """Главная страница - 10 последних опубликованных постов с пагинацией"""
    post_list = Post.objects.filter_published()  # published_only=True по умолчанию
    post_list = Post.objects.with_comments(post_list)  # Добавляем количество комментариев
    post_list = post_list.select_related(
        'author', 'location', 'category'
    ).order_by(*Post._meta.ordering)

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, pk):
    """Страница отдельной публикации"""
    # ПЕРВЫЙ вызов get_object_or_404: извлекаем пост по ключу из полной таблицы
    post = get_object_or_404(Post, pk=pk)
    
    # Проверяем, является ли пользователь автором
    if request.user == post.author:
        # Автор может видеть свой пост даже если он не опубликован
        comments = post.comments.all().order_by('created_at')
        form = CommentForm()
        
        context = {
            'post': post,
            'comments': comments,
            'form': form
        }
        return render(request, 'blog/detail.html', context)
    else:
        # ВТОРОЙ вызов get_object_or_404: для не-авторов проверяем опубликованность
        # Пытаемся получить тот же пост, но с условиями публикации
        try:
            published_post = get_object_or_404(
                Post.objects.filter(
                    is_published=True,
                    pub_date__lte=timezone.now(),
                    category__is_published=True
                ),
                pk=pk
            )
        except:
            # Если пост не найден в опубликованных, возвращаем 404
            return render(request, 'pages/404.html', status=404)
        
        comments = published_post.comments.all().order_by('created_at')
        form = CommentForm()
        
        context = {
            'post': published_post,
            'comments': comments,
            'form': form
        }
        return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    """Страница категории"""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    posts_from_category = category.posts.all()
    # Затем фильтруем по опубликованности
    post_list = Post.objects.filter_published(posts_from_category, published_only=True)
    # Добавляем количество комментариев
    post_list = Post.objects.with_comments(post_list)
    post_list = post_list.select_related('author', 'location', 'category').order_by(*Post._meta.ordering)

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj
    }
    return render(request, 'blog/category.html', context)


def profile(request, username):
    """Страница профиля пользователя"""
    user = get_object_or_404(User, username=username)
    published_only = (request.user != user)
    authors_posts = user.posts.all()  # ✅ Используем обратную связь
    posts = Post.objects.filter_published(authors_posts, published_only=published_only)
    # Добавляем количество комментариев
    posts = Post.objects.with_comments(posts)
    posts = posts.select_related('category', 'location', 'author').order_by(*Post._meta.ordering)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/profile.html', {
        'profile': user,
        'page_obj': page_obj
    })


@login_required
def create_post(request):
    """Создание нового поста"""
    form = PostForm(request.POST or None, request.FILES or None)
    
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    """Редактирование поста"""
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', pk=post_id)

    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', pk=post_id)
    
    return render(request, 'blog/create.html', {'form': form, 'post': post})


@login_required
def delete_post(request, post_id):
    """Удаление поста"""
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', pk=post_id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    return render(request, 'blog/create.html', {'form': PostForm(instance=post)})


@login_required
def add_comment(request, post_id):
    """Добавление комментария"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    
    return redirect('blog:post_detail', pk=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария"""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', pk=post_id)

    form = CommentForm(request.POST or None, instance=comment)
    
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', pk=post_id)
    
    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment
    })



@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария"""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', pk=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', pk=post_id)

    return render(request, 'blog/comment.html', {
        'comment': comment
    })


def signup(request):
    """Регистрация пользователя"""
    form = CreationForm(request.POST or None)
    
    if form.is_valid():
        form.save()
        return redirect('blog:index')
    
    return render(request, 'registration/registration_form.html', {'form': form})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditUserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(
                'blog:profile',
                username=request.user.username
            )
    else:
        form = EditUserForm(instance=request.user)

    return render(
        request,
        'blog/user.html',
        {
            'form': form,
            'form_class': EditUserForm,
        }
    )
