from lego.permissions.keyword_permissions import KeywordPermissions
from lego.permissions.object_permissions import ObjectPermissions


class CommentPermissions(KeywordPermissions, ObjectPermissions):
    perms_map = {
        'list': '/sudo/admin/comments/retrieve/',
        'retrieve': '/sudo/admin/comments/retrieve/',
        'create': '/sudo/admin/comments/create/',
        'update': '/sudo/admin/comments/update/',
        'partial_update': '/sudo/admin/comments/update/',
        'destroy': '/sudo/admin/comments/destroy/',
    }

    def has_object_permission(self, request, view, obj):
        # TODO: Check permissions of source
        return KeywordPermissions.has_object_permission(self, request, view, obj)