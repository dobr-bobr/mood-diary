from uuid import UUID

from mood_diary.backend.exceptions.user import (
    IncorrectPasswordOrUserDoesNotExists,
    InvalidOrExpiredRefreshToken,
    UserNotFound,
    IncorrectOldPassword,
    UsernameAlreadyExists,
)
from mood_diary.backend.repositories.sсhemas.user import (
    CreateUser,
    UpdateUserProfile,
    UpdateUserHashedPassword,
)
from mood_diary.backend.repositories.user import UserRepository
from mood_diary.backend.utils.password_hasher import PasswordHasher
from mood_diary.backend.utils.token_manager import TokenManager, TokenType
from mood_diary.common.api.schemas.auth import (
    RegisterRequest,
    Profile,
    LoginRequest,
    LoginResponse,
    RefreshResponse,
    RefreshRequest,
    ChangePasswordRequest,
    ChangeProfileRequest,
)


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_manager: TokenManager,
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_manager = token_manager

    async def register(self, body: RegisterRequest) -> Profile:
        create_user = CreateUser(
            username=body.username,
            hashed_password=self.password_hasher.hash(body.password),
            name=body.name,
        )

        user = await self.user_repository.create(create_user)

        if user is None:
            raise UsernameAlreadyExists()

        return Profile(
            id=user.id,
            username=user.username,
            name=user.name,
            created_at=user.created_at,
            updated_at=user.updated_at,
            password_updated_at=user.password_updated_at,
        )

    async def login(self, body: LoginRequest) -> LoginResponse:
        user = await self.user_repository.get_by_username(body.username)

        if not user or not self.password_hasher.verify(
            body.password, user.hashed_password
        ):
            raise IncorrectPasswordOrUserDoesNotExists()

        return LoginResponse(
            access_token=self.token_manager.create_token(TokenType.ACCESS, user.id),
            refresh_token=self.token_manager.create_token(TokenType.REFRESH, user.id),
        )

    async def refresh(self, body: RefreshRequest) -> RefreshResponse:
        token = self.token_manager.decode_token(body.refresh_token)

        if not token or token.type != TokenType.REFRESH:
            raise InvalidOrExpiredRefreshToken()

        return RefreshResponse(
            access_token=self.token_manager.create_token(
                TokenType.ACCESS, token.user_id
            ),
        )

    async def get_profile(self, user_id: UUID) -> Profile:
        user = await self.user_repository.get(user_id)

        if not user:
            raise UserNotFound()

        return Profile(
            id=user.id,
            username=user.username,
            name=user.name,
            created_at=user.created_at,
            updated_at=user.updated_at,
            password_updated_at=user.password_updated_at,
        )

    async def change_password(self, user_id: UUID, body: ChangePasswordRequest) -> None:
        user = await self.user_repository.get(user_id)

        if not user:
            raise UserNotFound()

        if not self.password_hasher.verify(body.old_password, user.hashed_password):
            raise IncorrectOldPassword()

        hashed_password = self.password_hasher.hash(body.new_password)

        update_user = UpdateUserHashedPassword(hashed_password=hashed_password)

        updated_user = await self.user_repository.update_hashed_password(
            user_id, update_user
        )

        if updated_user is None:
            raise UserNotFound()

    async def update_profile(
        self, user_id: UUID, body: ChangeProfileRequest
    ) -> Profile:
        user = await self.user_repository.get(user_id)

        if not user:
            raise UserNotFound()

        update_user = UpdateUserProfile(name=body.name)

        updated_user = await self.user_repository.update_profile(user_id, update_user)

        if updated_user is None:
            raise UserNotFound()

        return Profile(
            id=updated_user.id,
            username=updated_user.username,
            name=updated_user.name,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
            password_updated_at=updated_user.password_updated_at,
        )
