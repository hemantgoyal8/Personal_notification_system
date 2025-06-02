import strawberry
from typing import List, Optional

from .types import (
    UserType,
    AuthResponseType,
    NotificationType,
    MarkReadResponseType,
    UserRegisterInput,     
    UserUpdateInput,       
)


# Import your resolvers
from ..resolvers import (
    auth_resolvers, user_resolvers, notification_resolvers
    )

@strawberry.type
class Query:
    @strawberry.field(description="Get the currently authenticated user's details.")
    async def me(self, info: strawberry.Info) -> Optional[UserType]:
        return await user_resolvers.resolve_get_me(info)

    @strawberry.field(description="Get notifications for the authenticated user.")
    async def notifications(
        self,
        info: strawberry.Info,
        unread_only: bool = False,  # Python default value
        skip: int = 0,              # Python default value
        limit: int = 100            # Python default value
    ) -> List[NotificationType]:
        return await notification_resolvers.resolve_notifications_for_user(info, unread_only, skip, limit)

    # Example public query (if needed)
    # @strawberry.field
    # def health_check(self) -> str:
    #      return "Gateway OK"


@strawberry.type
class Mutation:
    @strawberry.mutation(description="Register a new user account.")
    async def register_user(self, info: strawberry.Info, user_in: UserRegisterInput) -> UserType:
        return await auth_resolvers.resolve_register_user(info, user_in)

    @strawberry.mutation(description="Log in a user to get an access token.")
    async def login(self, info: strawberry.Info, email: str, password: str) -> AuthResponseType:
        return await auth_resolvers.resolve_login(info, email, password)

    @strawberry.mutation(description="Update user preferences.")
    async def update_user_preferences(self, info: strawberry.Info, input: UserUpdateInput) -> Optional[UserType]: 
        return await user_resolvers.resolve_update_user_preferences(info, input)

    @strawberry.mutation(description="Mark a specific notification as read.")
    async def mark_notification_read(self, info: notification_resolvers.GraphQLContext, notification_id: str) -> NotificationType:
        # Authentication check is handled within the resolver
        return await notification_resolvers.resolve_mark_notification_read(info, notification_id)

    @strawberry.mutation(description="Mark all unread notifications for the user as read.")
    async def mark_all_notifications_read(self, info: notification_resolvers.GraphQLContext) -> MarkReadResponseType:
        # Authentication check is handled within the resolver
        return await notification_resolvers.resolve_mark_all_notifications_read(info)


# Create the final schema
schema = strawberry.Schema(query=Query, mutation=Mutation)