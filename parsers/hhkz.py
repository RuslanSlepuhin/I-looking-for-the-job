from parsers.hh import HH

class KZHH(HH):

    async def get_content(self, *args, **kwargs):
        self.base_url = "https://hh.kz"
        self.source_title_name = "HHKZ"
        await super().get_content(*args, **kwargs)

