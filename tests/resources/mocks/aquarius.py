from unittest.mock import Mock


class AquariusMock(Mock):
    ddo_list = []
    url = 'http://localhost:5000/api/v1/aquarius/assets/ddo'
    # def __init__(self, url, *args, **kwargs):
    #     Mock.__init__(self, *args, **kwargs)
    #     self.url = url

    @staticmethod
    def get_service_endpoint(did):
        return f'{AquariusMock.url}/{did}'

    def list_assets(self):
        return self.ddo_list

    @staticmethod
    def get_asset_ddo(did):
        return AquariusMock.ddo_list[0]

    @staticmethod
    def publish_asset_ddo(ddo):
        AquariusMock.ddo_list.append(ddo)

    def get_asset_metadata(self, did):
        return self.ddo_list[0].metadata
