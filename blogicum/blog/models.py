from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count

User = get_user_model()


class BaseModel(models.Model):
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)

    def __str__(self):
        return getattr(self, 'title', getattr(self, 'name', super().__str__()))


class Category(BaseModel):
    title = models.CharField(
        'Заголовок',
        max_length=256
    )
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text=(
            'Идентификатор страницы для URL; '
            'разрешены символы латиницы, цифры, дефис и подчёркивание.'
        )
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title


class Location(BaseModel):
    name = models.CharField(
        'Название места',
        max_length=256
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class PostManager(models.Manager):  # ИЗМЕНЕНО: добавлен кастомный менеджер
    """Кастомный менеджер для модели Post"""

    def filter_published(self, queryset=None, published_only=True):
        """
        Фильтрует переданный queryset по опубликованности.

        Args:
            queryset (QuerySet, optional): Набор постов для фильтрации. 
                По умолчанию None (все посты таблицы).
            published_only (bool): Если True, фильтрует только опубликованные посты
        """
        if queryset is None:
            queryset = self.get_queryset()  # По умолчанию - все посты таблицы

        if published_only:
            queryset = queryset.filter(
                is_published=True,
                pub_date__lte=timezone.now(),
                category__is_published=True
            )

        return queryset

    # ИЗМЕНЕНО: Добавлен метод with_comments, принимающий queryset
    def with_comments(self, queryset=None):
        """Добавляет количество комментариев к переданному queryset"""
        if queryset is None:
            queryset = self.get_queryset()  # По умолчанию - все посты таблицы

        return queryset.annotate(comment_count=Count('comments'))

    def get_posts_with_comments(self, published_only=True, category=None, author=None):
        """
        Возвращает посты с количеством комментариев.

        Args:
            published_only (bool): Если True, фильтрует только опубликованные посты
            category (Category): Если указана, фильтрует по категории
            author (User): Если указан, фильтрует по автору
        """
        qs = self.get_queryset()

        if published_only:
            qs = qs.filter(
                is_published=True,
                pub_date__lte=timezone.now(),
                category__is_published=True
            )

        if category:
            qs = qs.filter(category=category)

        if author:
            qs = qs.filter(author=author)

        return qs.annotate(comment_count=Count('comments'))


class Post(BaseModel):
    title = models.CharField(
        'Заголовок',
        max_length=256
    )
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='posts'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение',
        related_name='posts'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
        related_name='posts'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='posts_images/',
        blank=True
    )

    objects = PostManager()

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.title


class Comment(models.Model):
    text = models.TextField('Текст комментария')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Публикация'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'Комментарий {self.author} к {self.post}'
