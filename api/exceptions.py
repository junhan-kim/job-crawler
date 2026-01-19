from http import HTTPStatus

from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ErrorResponseKey:
    ERROR = "error"
    CODE = "code"
    MESSAGE = "message"


class ErrorCode:
    INTERNAL_SERVER_ERROR = "InternalServerError"


class ErrorMessage:
    UNEXPECTED = "An unexpected error occurred"


class ValidationError(APIException):
    status_code = HTTPStatus.BAD_REQUEST
    default_detail = "Invalid input"


class QueryRequiredError(ValidationError):
    default_detail = "query required"


class QueryTooLongError(ValidationError):
    default_detail = "query too long"


class LLMError(APIException):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    default_detail = "LLM service error"


class ServerBusyError(APIException):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    default_detail = "Server is busy. Please try again later."


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            ErrorResponseKey.ERROR: {
                ErrorResponseKey.CODE: exc.__class__.__name__,
                ErrorResponseKey.MESSAGE: str(exc.detail) if hasattr(exc, "detail") else str(exc),
            }
        }
        return response

    return Response(
        {
            ErrorResponseKey.ERROR: {
                ErrorResponseKey.CODE: ErrorCode.INTERNAL_SERVER_ERROR,
                ErrorResponseKey.MESSAGE: ErrorMessage.UNEXPECTED,
            }
        },
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )
