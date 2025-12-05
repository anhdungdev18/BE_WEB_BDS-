from .auth_views import *
from .post_views import *
from .category_views import *
from .posttype_views import *
__all__ = [
    'post_list', 'post_detail', 
    'category_list',
    'posttype_list',
    'register', 'login', 'logout'
]
