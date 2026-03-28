"""
Generador de PDFs para recibos de compra
"""

import io
import logging
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generador de PDFs para receipts y documentos."""

    COLORS = {
        'primary': colors.HexColor('#00FFFF'),
        'secondary': colors.HexColor('#FF00FF'),
        'accent': colors.HexColor('#FFFF00'),
        'success': colors.HexColor('#00FF00'),
        'warning': colors.HexColor('#FFA500'),
        'danger': colors.HexColor('#FF4444'),
        'dark': colors.HexColor('#1a1a2e'),
        'light': colors.HexColor('#f8f9fa'),
        'text': colors.HexColor('#333333'),
        'text_light': colors.HexColor('#666666'),
    }

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configura estilos personalizados."""
        self.styles.add(ParagraphStyle(
            name='NeonTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=self.COLORS['primary'],
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='NeonSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.COLORS['secondary'],
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='NeonBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COLORS['text'],
            alignment=TA_LEFT,
            spaceAfter=6,
            fontName='Helvetica'
        ))

        self.styles.add(ParagraphStyle(
            name='NeonSmall',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=self.COLORS['text_light'],
            alignment=TA_LEFT,
            spaceAfter=4,
            fontName='Helvetica'
        ))

        self.styles.add(ParagraphStyle(
            name='NeonRight',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COLORS['text'],
            alignment=TA_RIGHT,
            fontName='Helvetica'
        ))

    def _format_currency(self, amount, currency='CLP'):
        """Formatea un monto a moneda."""
        if currency == 'CLP':
            return f"${int(amount):,}"
        elif currency == 'USD':
            return f"${float(amount):,.2f}"
        elif currency == 'MXN':
            return f"${int(amount):,} MXN"
        return f"{currency} {amount}"

    def generate_order_receipt(self, order, buyer=None):
        """
        Genera un PDF receipt para una orden.
        
        Args:
            order: Instancia de Order
            buyer: Usuario comprador (opcional)
            
        Returns:
            Bytes del PDF
        """
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30*mm,
            leftMargin=30*mm,
            topMargin=30*mm,
            bottomMargin=30*mm
        )

        story = []

        story.append(Paragraph("LOGICPERFECT", self.styles['NeonTitle']))
        story.append(Paragraph("Comprobante de Compra", self.styles['NeonSubtitle']))
        story.append(Spacer(1, 10*mm))
        
        story.append(HRFlowable(
            width="100%",
            thickness=2,
            color=self.COLORS['primary'],
            spaceAfter=10
        ))
        
        info_data = [
            ['N° de Orden:', order.order_number, 'Fecha:', order.created_at.strftime('%d/%m/%Y %H:%M')],
            ['Estado:', self._get_status_text(order.status), 'Moneda:', order.currency],
        ]
        
        if buyer:
            info_data.insert(0, ['Cliente:', buyer.get_full_name() or buyer.email, 'Email:', buyer.email])
        
        info_table = Table(info_data, colWidths=[50*mm, 50*mm, 40*mm, 50*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), self.COLORS['text_light']),
            ('TEXTCOLOR', (2, 0), (2, -1), self.COLORS['text_light']),
            ('TEXTCOLOR', (1, 0), (1, -1), self.COLORS['text']),
            ('TEXTCOLOR', (3, 0), (3, -1), self.COLORS['text']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 10*mm))
        
        story.append(Paragraph("Detalle de la Compra", self.styles['Heading3']))
        story.append(Spacer(1, 3*mm))
        
        items_header = ['Producto', 'Vendedor', 'Licencia', 'Cant.', 'Precio Unit.', 'Subtotal']
        items_data = [items_header]
        
        for item in order.items.select_related('product', 'seller').all():
            items_data.append([
                item.product_name[:40] + ('...' if len(item.product_name) > 40 else ''),
                item.seller_name[:20],
                item.get_license_type_display() if hasattr(item, 'get_license_type_display') else item.license_type,
                str(item.quantity),
                self._format_currency(item.unit_price, order.currency),
                self._format_currency(item.subtotal, order.currency),
            ])
        
        items_table = Table(items_data, colWidths=[50*mm, 30*mm, 25*mm, 15*mm, 28*mm, 28*mm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['dark']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['primary']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (2, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['text_light']),
            ('BACKGROUND', (0, 1), (-1, -1), self.COLORS['light']),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLORS['light'], colors.white]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 8*mm))
        
        totals_data = [
            ['Subtotal:', self._format_currency(order.subtotal, order.currency)],
            ['Descuento:', f"- {self._format_currency(order.discount, order.currency)}" if order.discount > 0 else '$0'],
            ['IVA (19% Chile):', self._format_currency(order.iva_amount, order.currency)],
        ]
        
        totals_table = Table(totals_data, colWidths=[120*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(totals_table)
        
        story.append(Spacer(1, 3*mm))
        story.append(HRFlowable(width="100%", thickness=1, color=self.COLORS['primary']))
        story.append(Spacer(1, 3*mm))
        
        total_data = [['TOTAL:', self._format_currency(order.total, order.currency)]]
        total_table = Table(total_data, colWidths=[120*mm, 40*mm])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['success']),
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ]))
        story.append(total_table)
        story.append(Spacer(1, 10*mm))
        
        story.append(Paragraph("Distribución Financiera", self.styles['Heading3']))
        story.append(Spacer(1, 3*mm))
        
        if order.iva_amount or order.mercadopago_fee or order.platform_maintenance or order.seller_total:
            distribution_data = [
                ['Concepto', 'Monto', '%'],
            ]
            
            total = float(order.total)
            
            if order.iva_amount:
                pct = (float(order.iva_amount) / total * 100) if total else 0
                distribution_data.append(['IVA Chile (19%)', self._format_currency(order.iva_amount, order.currency), f'{pct:.1f}%'])
            
            if order.mercadopago_fee:
                pct = (float(order.mercadopago_fee) / total * 100) if total else 0
                distribution_data.append(['Comisión Mercado Pago', self._format_currency(order.mercadopago_fee, order.currency), f'{pct:.1f}%'])
            
            if order.platform_maintenance:
                pct = (float(order.platform_maintenance) / total * 100) if total else 0
                distribution_data.append(['Mantención Plataforma (15%)', self._format_currency(order.platform_maintenance, order.currency), f'{pct:.1f}%'])
            
            if order.seller_total:
                pct = (float(order.seller_total) / total * 100) if total else 0
                distribution_data.append(['Pago Neto Vendedor (64%)', self._format_currency(order.seller_total, order.currency), f'{pct:.1f}%'])
            
            dist_table = Table(distribution_data, colWidths=[80*mm, 40*mm, 30*mm])
            dist_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['dark']),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['accent']),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['text_light']),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLORS['light'], colors.white]),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(dist_table)
        
        story.append(Spacer(1, 15*mm))
        
        if order.mercadopago_payment_id:
            story.append(Paragraph("Información de Pago", self.styles['Heading3']))
            story.append(Spacer(1, 3*mm))
            payment_info = [
                ['Método de Pago:', 'Mercado Pago'],
                ['ID de Transacción:', order.mercadopago_payment_id],
                ['Fecha de Pago:', order.paid_at.strftime('%d/%m/%Y %H:%M') if order.paid_at else 'N/A'],
            ]
            payment_table = Table(payment_info, colWidths=[50*mm, 100*mm])
            payment_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (0, -1), self.COLORS['text_light']),
                ('TEXTCOLOR', (1, 0), (1, -1), self.COLORS['text']),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(payment_table)
        
        story.append(Spacer(1, 20*mm))
        story.append(HRFlowable(width="100%", thickness=1, color=self.COLORS['primary']))
        story.append(Spacer(1, 5*mm))
        
        story.append(Paragraph(
            "Gracias por tu compra en LogicPerfect. Este documento es tu comprobante oficial.",
            self.styles['NeonSmall']
        ))
        story.append(Paragraph(
            f"Generado el {timezone.now().strftime('%d/%m/%Y a las %H:%M')}",
            self.styles['NeonSmall']
        ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_seller_report(self, seller, start_date=None, end_date=None, orders=None):
        """
        Genera un reporte de ventas para vendedores.
        
        Args:
            seller: Usuario vendedor
            start_date: Fecha de inicio
            end_date: Fecha de fin
            orders: QuerySet de órdenes
            
        Returns:
            Bytes del PDF
        """
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30*mm,
            leftMargin=30*mm,
            topMargin=30*mm,
            bottomMargin=30*mm
        )
        
        story = []
        
        story.append(Paragraph("LOGICPERFECT", self.styles['NeonTitle']))
        story.append(Paragraph("Reporte de Ventas", self.styles['NeonSubtitle']))
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph(f"Vendedor: {seller.get_full_name() or seller.email}", self.styles['NeonBody']))
        
        if start_date and end_date:
            story.append(Paragraph(
                f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
                self.styles['NeonSmall']
            ))
        
        story.append(Spacer(1, 10*mm))
        story.append(HRFlowable(width="100%", thickness=2, color=self.COLORS['secondary']))
        story.append(Spacer(1, 10*mm))
        
        if orders:
            total_sales = sum(float(o.total) for o in orders)
            total_items = sum(o.items.count() for o in orders)
            total_iva = sum(float(o.iva_amount) for o in orders)
            total_commission = sum(float(o.mercadopago_fee) + float(o.platform_maintenance) for o in orders)
            net_earnings = sum(float(o.seller_total) for o in orders)
            
            summary_data = [
                ['Resumen de Ventas', ''],
                ['Total de Órdenes:', str(orders.count())],
                ['Productos Vendidos:', str(total_items)],
                ['Ventas Brutas:', self._format_currency(total_sales, 'CLP')],
                ['IVA Cobrado:', self._format_currency(total_iva, 'CLP')],
                ['Comisiones:', f"- {self._format_currency(total_commission, 'CLP')}"],
                ['Ganancia Neta:', self._format_currency(net_earnings, 'CLP')],
            ]
            
            summary_table = Table(summary_data, colWidths=[80*mm, 60*mm])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['success']),
                ('SPAN', (0, 0), (-1, 0)),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (0, 1), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['text_light']),
                ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['dark']),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(summary_table)
        
        story.append(Spacer(1, 15*mm))
        
        story.append(Paragraph(
            f"Generado el {timezone.now().strftime('%d/%m/%Y a las %H:%M')}",
            self.styles['NeonSmall']
        ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def _get_status_text(status):
        """Obtiene texto legible del estado."""
        status_map = {
            'pending': 'Pendiente',
            'paid': 'Pagado',
            'processing': 'Procesando',
            'completed': 'Completado',
            'cancelled': 'Cancelado',
            'refunded': 'Reembolsado',
            'failed': 'Fallido',
        }
        return status_map.get(status, status.capitalize())


def generate_order_pdf(order, buyer=None):
    """Función helper para generar PDF de orden."""
    generator = PDFGenerator()
    return generator.generate_order_receipt(order, buyer)


def generate_seller_pdf(seller, start_date=None, end_date=None, orders=None):
    """Función helper para generar PDF de reporte de vendedor."""
    generator = PDFGenerator()
    return generator.generate_seller_report(seller, start_date, end_date, orders)
