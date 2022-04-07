from io import BytesIO
import xlsxwriter


class AfpExcelReport(object):

    def __init__(self, data, obj):
        self.data = data
        self.obj = obj

    def get_filename(self):
        return 'AFPNET.xlsx'

    def get_content(self):
        output = BytesIO()
        wb = xlsxwriter.Workbook(output, {
            'default_date_format': 'dd/mm/yyyy'
        })
        sheet = wb.add_worksheet('TRABAJADOR')
        content_table_format = wb.add_format({
            'size': 10,
        })
        sheet.set_column('B:G', 15)
        sheet.write(0, 0, 'N', content_table_format)
        sheet.write(0, 1, 'Código único (CUSPP)', content_table_format)
        sheet.write(0, 2, 'Tipo de documento', content_table_format)
        sheet.write(0, 3, 'Número de documento', content_table_format)
        sheet.write(0, 4, 'Apellido paterno', content_table_format)
        sheet.write(0, 5, 'Apellido materno', content_table_format)
        sheet.write(0, 6, 'Nomhres', content_table_format)
        sheet.write(0, 7, 'Relación laboral', content_table_format)
        sheet.write(0, 8, 'Inicio relación laboral', content_table_format)
        sheet.write(0, 9, 'Fin relación laboral', content_table_format)
        sheet.write(0, 10, 'Excepción de aportar', content_table_format)
        sheet.write(0, 11, 'Remuneración asegurable', content_table_format)
        sheet.write(0, 12, 'Aporte voluntario con fin previsiona', content_table_format)
        sheet.write(0, 13, 'Aporte voluntario sin fin previsional', content_table_format)
        sheet.write(0, 14, 'Aporte voluntario del empleador', content_table_format)
        sheet.write(0, 15, 'Tipo de trabajo', content_table_format)
        sheet.write(0, 16, 'AFP', content_table_format)
        row = 1
        for val in self.data:
            sheet.write(row, 0, row + 1, content_table_format)
            sheet.write(row, 1, val['cuspp'], content_table_format)
            sheet.write(row, 2, val['document_type_id'], content_table_format)
            sheet.write(row, 3, val['document_number'], content_table_format)
            sheet.write(row, 4, val['lastname'], content_table_format)
            sheet.write(row, 5, val['secondname'], content_table_format)
            sheet.write(row, 6, val['firstname'], content_table_format)
            sheet.write(row, 7, val['business_relation'], content_table_format)
            sheet.write(row, 8, val['begin_business_relation'], content_table_format)
            sheet.write(row, 9, val['end_business_relation'], content_table_format)
            sheet.write(row, 10, val['except_amount'], content_table_format)
            sheet.write(row, 11, val['rem'], content_table_format)
            sheet.write(row, 12, val['amount_vol_fin'], content_table_format)
            sheet.write(row, 13, val['amount_vol_nfin'], content_table_format)
            sheet.write(row, 14, val['amount_vol'], content_table_format)
            sheet.write(row, 15, val['work_type'], content_table_format)
            sheet.write(row, 16, val['afp'], content_table_format)
            row += 1

        wb.close()
        output.seek(0)
        return output.read()
