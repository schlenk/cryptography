# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import, division, print_function

import os

import pytest

from cryptography import x509
from cryptography.hazmat.backends.interfaces import RSABackend, X509Backend

from .test_x509 import _load_cert


class TestExtension(object):
    def test_not_an_oid(self):
        bc = x509.BasicConstraints(ca=False, path_length=None)
        with pytest.raises(TypeError):
            x509.Extension("notanoid", True, bc)

    def test_critical_not_a_bool(self):
        bc = x509.BasicConstraints(ca=False, path_length=None)
        with pytest.raises(TypeError):
            x509.Extension(x509.OID_BASIC_CONSTRAINTS, "notabool", bc)

    def test_repr(self):
        bc = x509.BasicConstraints(ca=False, path_length=None)
        ext = x509.Extension(x509.OID_BASIC_CONSTRAINTS, True, bc)
        assert repr(ext) == (
            "<Extension(oid=<ObjectIdentifier(oid=2.5.29.19, name=basicConst"
            "raints)>, critical=True, value=<BasicConstraints(ca=False, path"
            "_length=None)>)>"
        )


class TestKeyUsage(object):
    def test_key_agreement_false_encipher_decipher_true(self):
        with pytest.raises(ValueError):
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=True,
                decipher_only=False
            )

        with pytest.raises(ValueError):
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=True,
                decipher_only=True
            )

        with pytest.raises(ValueError):
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=True
            )

    def test_properties_key_agreement_true(self):
        ku = x509.KeyUsage(
            digital_signature=True,
            content_commitment=True,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False
        )
        assert ku.digital_signature is True
        assert ku.content_commitment is True
        assert ku.key_encipherment is False
        assert ku.data_encipherment is False
        assert ku.key_agreement is False
        assert ku.key_cert_sign is True
        assert ku.crl_sign is False

    def test_key_agreement_true_properties(self):
        ku = x509.KeyUsage(
            digital_signature=False,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=True,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=True
        )
        assert ku.key_agreement is True
        assert ku.encipher_only is False
        assert ku.decipher_only is True

    def test_key_agreement_false_properties(self):
        ku = x509.KeyUsage(
            digital_signature=False,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False
        )
        assert ku.key_agreement is False
        with pytest.raises(ValueError):
            ku.encipher_only

        with pytest.raises(ValueError):
            ku.decipher_only


class TestBasicConstraints(object):
    def test_ca_not_boolean(self):
        with pytest.raises(TypeError):
            x509.BasicConstraints(ca="notbool", path_length=None)

    def test_path_length_not_ca(self):
        with pytest.raises(ValueError):
            x509.BasicConstraints(ca=False, path_length=0)

    def test_path_length_not_int(self):
        with pytest.raises(TypeError):
            x509.BasicConstraints(ca=True, path_length=1.1)

        with pytest.raises(TypeError):
            x509.BasicConstraints(ca=True, path_length="notint")

    def test_path_length_negative(self):
        with pytest.raises(TypeError):
            x509.BasicConstraints(ca=True, path_length=-1)

    def test_repr(self):
        na = x509.BasicConstraints(ca=True, path_length=None)
        assert repr(na) == (
            "<BasicConstraints(ca=True, path_length=None)>"
        )


class TestExtendedKeyUsage(object):
    def test_not_all_oids(self):
        with pytest.raises(TypeError):
            x509.ExtendedKeyUsage(["notoid"])

    def test_iter_len(self):
        eku = x509.ExtendedKeyUsage([
            x509.ObjectIdentifier("1.3.6.1.5.5.7.3.1"),
            x509.ObjectIdentifier("1.3.6.1.5.5.7.3.2"),
        ])
        assert len(eku) == 2
        assert list(eku) == [
            x509.OID_SERVER_AUTH,
            x509.OID_CLIENT_AUTH
        ]

    def test_repr(self):
        eku = x509.ExtendedKeyUsage([
            x509.ObjectIdentifier("1.3.6.1.5.5.7.3.1"),
            x509.ObjectIdentifier("1.3.6.1.5.5.7.3.2"),
        ])
        assert repr(eku) == (
            "<ExtendedKeyUsage([<ObjectIdentifier(oid=1.3.6.1.5.5.7.3.1, name="
            "serverAuth)>, <ObjectIdentifier(oid=1.3.6.1.5.5.7.3.2, name=clien"
            "tAuth)>])>"
        )


@pytest.mark.requires_backend_interface(interface=RSABackend)
@pytest.mark.requires_backend_interface(interface=X509Backend)
class TestExtensions(object):
    def test_no_extensions(self, backend):
        cert = _load_cert(
            os.path.join("x509", "verisign_md2_root.pem"),
            x509.load_pem_x509_certificate,
            backend
        )
        ext = cert.extensions
        assert len(ext) == 0
        assert list(ext) == []
        with pytest.raises(x509.ExtensionNotFound) as exc:
            ext.get_extension_for_oid(x509.OID_BASIC_CONSTRAINTS)

        assert exc.value.oid == x509.OID_BASIC_CONSTRAINTS

    def test_one_extension(self, backend):
        cert = _load_cert(
            os.path.join(
                "x509", "custom", "basic_constraints_not_critical.pem"
            ),
            x509.load_pem_x509_certificate,
            backend
        )
        extensions = cert.extensions
        ext = extensions.get_extension_for_oid(x509.OID_BASIC_CONSTRAINTS)
        assert ext is not None
        assert ext.value.ca is False

    def test_duplicate_extension(self, backend):
        cert = _load_cert(
            os.path.join(
                "x509", "custom", "two_basic_constraints.pem"
            ),
            x509.load_pem_x509_certificate,
            backend
        )
        with pytest.raises(x509.DuplicateExtension) as exc:
            cert.extensions

        assert exc.value.oid == x509.OID_BASIC_CONSTRAINTS

    def test_unsupported_critical_extension(self, backend):
        cert = _load_cert(
            os.path.join(
                "x509", "custom", "unsupported_extension_critical.pem"
            ),
            x509.load_pem_x509_certificate,
            backend
        )
        with pytest.raises(x509.UnsupportedExtension) as exc:
            cert.extensions

        assert exc.value.oid == x509.ObjectIdentifier("1.2.3.4")

    def test_unsupported_extension(self, backend):
        # TODO: this will raise an exception when all extensions are complete
        cert = _load_cert(
            os.path.join(
                "x509", "custom", "unsupported_extension.pem"
            ),
            x509.load_pem_x509_certificate,
            backend
        )
        extensions = cert.extensions
        assert len(extensions) == 0


@pytest.mark.requires_backend_interface(interface=RSABackend)
@pytest.mark.requires_backend_interface(interface=X509Backend)
class TestBasicConstraintsExtension(object):
    def test_ca_true_pathlen_6(self, backend):
        cert = _load_cert(
            os.path.join(
                "x509", "PKITS_data", "certs", "pathLenConstraint6CACert.crt"
            ),
            x509.load_der_x509_certificate,
            backend
        )
        ext = cert.extensions.get_extension_for_oid(
            x509.OID_BASIC_CONSTRAINTS
        )
        assert ext is not None
        assert ext.critical is True
        assert ext.value.ca is True
        assert ext.value.path_length == 6

    def test_path_length_zero(self, backend):
        cert = _load_cert(
            os.path.join("x509", "custom", "bc_path_length_zero.pem"),
            x509.load_pem_x509_certificate,
            backend
        )
        ext = cert.extensions.get_extension_for_oid(
            x509.OID_BASIC_CONSTRAINTS
        )
        assert ext is not None
        assert ext.critical is True
        assert ext.value.ca is True
        assert ext.value.path_length == 0

    def test_ca_true_no_pathlen(self, backend):
        cert = _load_cert(
            os.path.join("x509", "PKITS_data", "certs", "GoodCACert.crt"),
            x509.load_der_x509_certificate,
            backend
        )
        ext = cert.extensions.get_extension_for_oid(
            x509.OID_BASIC_CONSTRAINTS
        )
        assert ext is not None
        assert ext.critical is True
        assert ext.value.ca is True
        assert ext.value.path_length is None

    def test_ca_false(self, backend):
        cert = _load_cert(
            os.path.join("x509", "cryptography.io.pem"),
            x509.load_pem_x509_certificate,
            backend
        )
        ext = cert.extensions.get_extension_for_oid(
            x509.OID_BASIC_CONSTRAINTS
        )
        assert ext is not None
        assert ext.critical is True
        assert ext.value.ca is False
        assert ext.value.path_length is None

    def test_no_basic_constraints(self, backend):
        cert = _load_cert(
            os.path.join(
                "x509",
                "PKITS_data",
                "certs",
                "ValidCertificatePathTest1EE.crt"
            ),
            x509.load_der_x509_certificate,
            backend
        )
        with pytest.raises(x509.ExtensionNotFound):
            cert.extensions.get_extension_for_oid(x509.OID_BASIC_CONSTRAINTS)

    def test_basic_constraint_not_critical(self, backend):
        cert = _load_cert(
            os.path.join(
                "x509", "custom", "basic_constraints_not_critical.pem"
            ),
            x509.load_pem_x509_certificate,
            backend
        )
        ext = cert.extensions.get_extension_for_oid(
            x509.OID_BASIC_CONSTRAINTS
        )
        assert ext is not None
        assert ext.critical is False
        assert ext.value.ca is False
