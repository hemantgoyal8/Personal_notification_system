import strawberry
from typing import List

# Import your types
from .types import (
    UserType, AuthResponseType, NotificationType, MarkReadResponseType,
    UserRegisterInput, UserUpdateInput
)

# Import your resolvers
from graphql_gateway.app.resolvers import auth_resolvers, user_resolvers, notification_resolvers

@strawberry.type
class Query:
    @strawberry.field(description="Get the currently authenticated user's details.")
    async def me(self, info: notification_resolvers.GraphQLContext) -> UserType:
        # Authentication check is handled within the resolver
        return await user_resolvers.resolve_get_me(info)

    @strawberry.field(description="Get notifications for the authenticated user.")
    async def notifications(
        self, info: notification_resolvers.GraphQLContext,
        unread_only: bool = strawberry.argument(description="Fetch only unread notifications", default=False),
        skip: int = strawberry.argument(description="Number of notifications to skip (for pagination)", default=0),
        limit: int = strawberry.argument(description="Max number of notifications to return (for pagination)", default=100)
    ) -> List[NotificationType]:
         # Authentication check is handled within the resolver
        return await notification_resolvers.resolve_get_notifications(info, unread_only, skip, limit)

    # Example public query (if needed)
    # @strawberry.field
    # def health_check(self) -> str:
    #      return "Gateway OK"


@strawberry.type
class Mutation:
    @strawberry.mutation(description="Register a new user account.")
    async def register_user(self, user_in: UserRegisterInput) -> UserType:
        return await auth_resolvers.resolve_register_user(user_in)

    @strawberry.mutation(description="Log in a user to get an access token.")
    async def login(self, email: str, password: str) -> AuthResponseType:
        return await auth_resolvers.resolve_login(email, password)

    @strawberry.mutation(description="Update the authenticated user's details.")
    async def update_user(self, info: user_resolvers.GraphQLContext, user_in: UserUpdateInput) -> UserType:
        # Authentication check is handled within the resolver
        return await user_resolvers.resolve_update_user(info, user_in)

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