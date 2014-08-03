from critiquebrainz.data.testing import DataTestCase
from critiquebrainz.data import db
from license import License


class LicenceTestCase(DataTestCase):

    def test_licence_creation(self):
        license = License(id=u"Test", full_name=u'Test License')
        db.session.add(license)
        db.session.commit()
        assert License.query.count() == 1

    def test_licence_removal(self):
        license = License(id=u"Test", full_name=u'Test License')
        db.session.add(license)
        db.session.commit()

        assert License.query.count() == 1
        license.delete()
        assert License.query.count() == 0
