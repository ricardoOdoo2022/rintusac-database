class PlameReport(object):

    def __init__(self, rem_data, jor_data, snl_data, for_data, filename, obj):
        self.rem_data = rem_data
        self.jor_data = jor_data
        self.snl_data = snl_data
        self.for_data = for_data
        self.filename = filename
        self.obj = obj

    def get_filename(self, file_type):
        if file_type == 'rem':
            filename = '{}.rem'.format(self.filename)
        elif file_type == 'jor':
            filename = '{}.jor'.format(self.filename)
        elif file_type == 'for':
            filename = '{}.for'.format(self.filename)
        else:
            filename = '{}.snl'.format(self.filename)
        return filename

    def get_content_rem(self):
        raw = ''
        template = '{document_type}|{document_number}|{plame_code}|' \
                   '{amount}|{paid_amount}|\r\n'

        for value in self.rem_data:
            raw += template.format(
                document_type=value['document_type'],
                document_number=value['document_number'],
                plame_code=value['plame_code'],
                amount=value['amount'],
                paid_amount=value['paid_amount']
            )
        return raw.encode('utf8')

    def get_content_jor(self):
        raw = ''
        template = '{document_type}|{document_number}|{ord_hours}|' \
                   '{ord_min}|{hours_extra}|{min_extra}|\r\n'

        for value in self.jor_data:
            raw += template.format(
                document_type=value['document_type'],
                document_number=value['document_number'],
                ord_hours=value['ord_hours'],
                ord_min=value['ord_min'],
                hours_extra=value['hours_extra'],
                min_extra=value['min_extra']
            )
        return raw.encode('utf8')

    def get_content_snl(self):
        raw = ''
        template = '{document_type}|{document_number}|{code}|{days}|\r\n'

        for value in self.snl_data:
            raw += template.format(
                document_type=value['document_type'],
                document_number=value['document_number'],
                code=value['code'],
                days=value['days'],
            )
        return raw.encode('utf8')

    def get_content_for(self):
        raw = ''
        template = '{document_type}|{document_number}|{net_val}|\r\n'

        for value in self.for_data:
            raw += template.format(
                document_type=value['document_type'],
                document_number=value['document_number'],
                net_val=value['net_val']
            )
        return raw.encode('utf8')
