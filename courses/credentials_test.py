"""Credentials tests"""
from urllib.parse import urljoin

import pytest
from django.db.models.signals import post_save
from factory.django import mute_signals
from mitol.common.pytest_utils import any_instance_of
from mitol.digitalcredentials.factories import (
    DigitalCredentialRequestFactory,
    LearnerDIDFactory,
)
from mitol.digitalcredentials.models import DigitalCredentialRequest

from courses.credentials import (
    build_course_run_credential,
    build_digital_credential,
    build_program_credential,
    create_and_notify_digital_credential_request,
)
from courses.factories import (
    CourseFactory,
    CourseRunCertificateFactory,
    CourseRunFactory,
    ProgramCertificateFactory,
    ProgramFactory,
)


pytestmark = pytest.mark.django_db


def test_build_program_credential():
    """Build a program run completion object"""
    certificate = ProgramCertificateFactory.create()
    start_date, end_date = certificate.start_end_dates
    program = certificate.program
    assert build_program_credential(certificate) == {
        "type": "schema:EducationalOccupationalProgram",
        "identifier": program.text_id,
        "name": program.title,
        "description": program.page.description,
        "numberOfCredits": {"value": program.page.certificate_page.CEUs},
        "startDate": start_date,
        "endDate": end_date,
        "educationalCredentialAwarded": {
            "type": "schema:EducationalOccupationalCredential",
            "name": f"{program.title} Completion",
            "description": "",
        },
    }


def test_build_course_run_credential():
    """Build a course run completion object"""
    certificate = CourseRunCertificateFactory.create()
    course_run = certificate.course_run
    assert build_course_run_credential(certificate) == {
        "type": "schema:Course",
        "courseCode": course_run.course.readable_id,
        "name": course_run.course.title,
        "description": course_run.course.page.description,
        "numberOfCredits": {"value": course_run.course.page.certificate_page.CEUs},
        "startDate": course_run.start_date,
        "endDate": course_run.end_date,
    }


def test_build_digital_credential_course_run(settings, mocker):
    "Verify build_digital_credential works correctly for a course run"
    mock_build_course_run_credential = mocker.patch(
        "courses.credentials.build_course_run_credential", autospec=True
    )
    course_run = CourseRunFactory.create()
    learner_did = LearnerDIDFactory.create()
    certificate = CourseRunCertificateFactory.create(
        user=learner_did.learner, course_run=course_run
    )

    assert build_digital_credential(certificate, learner_did) == {
        "credential": {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://w3c-ccg.github.io/vc-ed-models/contexts/v1/context.json",
            ],
            "id": urljoin(settings.SITE_BASE_URL, certificate.link),
            "type": ["VerifiableCredential", "Assertion"],
            "issuer": {
                "type": "Issuer",
                "id": settings.DIGITAL_CREDENTIALS_ISSUER_ID,
                "name": settings.SITE_NAME,
                "url": settings.SITE_BASE_URL,
            },
            "issuanceDate": any_instance_of(str),
            "credentialSubject": {
                "type": "schema:Person",
                "id": learner_did.did,
                "name": learner_did.learner.name,
                "hasCredential": mock_build_course_run_credential.return_value,
            },
        },
        "options": {
            "verificationMethod": settings.DIGITAL_CREDENTIALS_VERIFICATION_METHOD
        },
    }

    mock_build_course_run_credential.assert_called_once_with(certificate)


def test_build_digital_credential_program_run(settings, mocker):
    "Verify build_digital_credential works correctly for a program run"
    mock_build_program_credential = mocker.patch(
        "courses.credentials.build_program_credential", autospec=True
    )
    program = ProgramFactory.create()
    learner_did = LearnerDIDFactory.create()
    certificate = ProgramCertificateFactory.create(
        user=learner_did.learner, program=program
    )

    assert build_digital_credential(certificate, learner_did) == {
        "credential": {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://w3c-ccg.github.io/vc-ed-models/contexts/v1/context.json",
            ],
            "id": urljoin(settings.SITE_BASE_URL, certificate.link),
            "type": ["VerifiableCredential", "Assertion"],
            "issuer": {
                "type": "Issuer",
                "id": settings.DIGITAL_CREDENTIALS_ISSUER_ID,
                "name": settings.SITE_NAME,
                "url": settings.SITE_BASE_URL,
            },
            "issuanceDate": any_instance_of(str),
            "credentialSubject": {
                "type": "schema:Person",
                "id": learner_did.did,
                "name": learner_did.learner.name,
                "hasCredential": mock_build_program_credential.return_value,
            },
        },
        "options": {
            "verificationMethod": settings.DIGITAL_CREDENTIALS_VERIFICATION_METHOD
        },
    }
    mock_build_program_credential.assert_called_once_with(certificate)


def test_test_build_digital_credential_invalid_certified_object(mocker):
    """Verify an exception is raised for an invalid courseware object"""
    invalid_courseware = CourseFactory.create()
    with pytest.raises(Exception):
        build_digital_credential(invalid_courseware, mocker.Mock())


@pytest.mark.parametrize(
    "certificate_factory", [ProgramCertificateFactory, CourseRunCertificateFactory]
)
@pytest.mark.parametrize("exists", [True, False])
@pytest.mark.parametrize("enabled", [True, False])
def test_create_and_notify_digital_credential_request(
    settings, mocker, user, certificate_factory, exists, enabled
):  # pylint: disable=too-many-arguments
    """Test create_and_notify_digital_credential_request"""
    settings.FEATURES["DIGITAL_CREDENTIALS"] = enabled
    mocker.patch(
        "courses.credentials.transaction.on_commit",
        side_effect=lambda callback: callback(),
    )
    mock_notify_digital_credential_request = mocker.patch(
        "courses.credentials.notify_digital_credential_request", autospec=True
    )

    with mute_signals(post_save):
        certificate = certificate_factory.create(user=user)
    if exists:
        DigitalCredentialRequestFactory.create(
            learner=user, credentialed_object=certificate
        )

    create_and_notify_digital_credential_request(certificate)

    if not exists and not enabled:
        assert DigitalCredentialRequest.objects.count() == 0
    elif exists:
        mock_notify_digital_credential_request.assert_not_called()
    else:
        credential_request = DigitalCredentialRequest.objects.get(learner=user)
        mock_notify_digital_credential_request.delay.assert_called_once_with(
            credential_request.id
        )
