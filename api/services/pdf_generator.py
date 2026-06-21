import os
import base64
from weasyprint import HTML

UPLOAD_DIR = "/app/uploads/invoices"
LOGO_PATH = "/app/uploads/logo.png"

def get_logo_base64():
    try:
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

def generate_invoice_pdf(invoice: dict, motors: list[dict]) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    motor_rows = "".join(
        f"""
        <tr>
            <td>{m.get('serial_number', 'N/A')}</td>
            <td>&nbsp;</td>
            <td style="text-align: right;">{invoice.get('subtotal', 0) / len(motors):,.2f}</td>
            <td style="text-align: right;">{invoice.get('subtotal', 0) / len(motors):,.2f}</td>
        </tr>
        """ for m in motors
    ) if motors else ""
    
    subtotal = float(invoice.get('subtotal', 0))
    discount = float(invoice.get('discount', 0))
    vat = float(invoice.get('vat', 0))
    total = float(invoice.get('total', 0))
    
    logo_base64 = get_logo_base64()
    logo_src = f"data:image/png;base64,{logo_base64}" if logo_base64 else ""
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Simons MC P.L.C - Attachment</title>
        <style>
            :root {{
                --primary-purple: #351c42;
                --logo-orange: #f3ab2a;
                --logo-red: #b0463c;
                --text-dark: #222222;
                --line-color: #999999;
                --table-border: #888888;
                --watermark-color: rgba(53, 28, 66, 0.04);
            }}

            * {{
                box-sizing: border-box;
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}

            @page {{
                size: A4;
                margin: 0;
            }}

            body {{
                background-color: #f0f2f5;
                padding: 40px 0;
                color: var(--text-dark);
                font-size: 14px;
            }}

            .document-container {{
                position: relative;
                background-color: #ffffff;
                width: 210mm;
                height: 297mm;
                margin: 0 auto;
                padding: 22mm 18mm;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
                box-sizing: border-box;
                overflow: hidden;
            }}

            .watermark-text-diagonal {{
                position: absolute;
                top: 48%;
                left: 50%;
                width: 100%;
                text-align: center;
                transform: translate(-50%, -50%) rotate(-15deg);
                font-size: 85px;
                font-weight: 900;
                color: var(--watermark-color);
                letter-spacing: 12px;
                pointer-events: none;
                text-transform: uppercase;
                white-space: nowrap;
                z-index: 1;
            }}

            .watermark-text-bottom {{
                position: absolute;
                bottom: 18%;
                left: 50%;
                transform: translateX(-50%);
                font-size: 76px;
                font-weight: 800;
                color: var(--watermark-color);
                letter-spacing: 4px;
                pointer-events: none;
                white-space: nowrap;
                z-index: 1;
            }}

            .content {{
                position: relative;
                z-index: 2;
                height: 100%;
            }}

            .header-table {{
                display: table;
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 25px;
            }}

            .header-row {{
                display: table-row;
            }}

            .header-left {{
                display: table-cell;
                width: 55%;
                vertical-align: top;
                text-align: center;
            }}

            .header-right {{
                display: table-cell;
                width: 45%;
                vertical-align: top;
                text-align: right;
                color: var(--primary-purple);
            }}

            .main-title {{
                font-size: 36px;
                font-weight: 900;
                letter-spacing: 1px;
                margin-bottom: 12px;
                color: var(--primary-purple);
            }}

            .info-line {{
                font-size: 14px;
                font-weight: 700;
                margin-bottom: 4px;
                letter-spacing: 0.3px;
            }}

            .date-section {{
                text-align: right;
                margin-bottom: 15px;
            }}

            .date-label {{
                display: inline-block;
                font-size: 14px;
                font-weight: bold;
            }}

            .date-underline {{
                display: inline-block;
                width: 160px;
                border-bottom: 1px solid var(--line-color);
                margin-left: 5px;
                vertical-align: bottom;
                height: 18px;
            }}

            .customer-table {{
                display: table;
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 25px;
            }}

            .customer-row {{
                display: table-row;
            }}

            .customer-cell-label {{
                display: table-cell;
                font-weight: bold;
                font-size: 14px;
                white-space: nowrap;
                padding-right: 8px;
                padding-bottom: 12px;
                width: 1%;
            }}

            .customer-cell-line {{
                display: table-cell;
                border-bottom: 1px solid var(--line-color);
                padding-bottom: 12px;
            }}

            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 25px;
            }}

            .data-table th {{
                background-color: var(--primary-purple);
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 12px 8px;
                text-align: center;
                border: 1px solid var(--primary-purple);
            }}

            .data-table th:first-child {{
                text-align: left;
                padding-left: 15px;
            }}

            .data-table td {{
                border: 1px solid var(--table-border);
                height: 50px;
                vertical-align: middle;
            }}

            .col-desc {{ width: 50%; }}
            .col-qty {{ width: 13%; }}
            .col-price {{ width: 17%; }}
            .col-total {{ width: 20%; }}

            .footer-table {{
                display: table;
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 35px;
            }}

            .footer-row {{
                display: table-row;
            }}

            .footer-left {{
                display: table-cell;
                width: 50%;
                vertical-align: top;
            }}

            .footer-right {{
                display: table-cell;
                width: 50%;
                vertical-align: top;
            }}

            .payment-box {{
                display: table;
                width: 90%;
                margin-top: 5px;
            }}

            .payment-row {{
                display: table-row;
            }}

            .payment-label {{
                display: table-cell;
                font-weight: bold;
                font-size: 13.5px;
                white-space: nowrap;
                width: 1%;
            }}

            .payment-line {{
                display: table-cell;
                border-bottom: 1px solid var(--line-color);
                height: 18px;
            }}

            .totals-table {{
                display: table;
                width: 80%;
                margin-left: auto;
            }}

            .totals-row {{
                display: table-row;
            }}

            .totals-label-cell {{
                display: table-cell;
                font-weight: bold;
                font-size: 13px;
                white-space: nowrap;
                padding-bottom: 12px;
                text-align: left;
                width: 1%;
            }}

            .totals-line-cell {{
                display: table-cell;
                border-bottom: 1px solid var(--line-color);
                padding-bottom: 12px;
            }}

            .signatures-container {{
                text-align: right;
                margin-top: 15px;
            }}

            .sig-block {{
                display: inline-block;
                width: 140px;
                text-align: center;
                margin-left: 80px;
                vertical-align: top;
            }}

            .sig-line {{
                border-bottom: 1px solid var(--line-color);
                height: 35px;
                margin-bottom: 8px;
            }}

            .sig-label {{
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 0.8px;
            }}

            @media print {{
                body {{
                    background-color: #ffffff;
                    padding: 0;
                    margin: 0;
                }}
                .document-container {{
                    width: 210mm;
                    height: 297mm;
                    margin: 0;
                    padding: 22mm 18mm;
                    border: none;
                    box-shadow: none;
                }}
            }}
        </style>
    </head>
    <body>

        <div class="document-container">
            
            <div class="watermark-text-diagonal">ATTACHMENT</div>
            <div class="watermark-text-bottom">SIMONS MC P.L.C</div>

            <div class="content">
                
                <div class="header-table">
                    <div class="header-row">
                        <div class="header-left">
                            <img src="{logo_src}" style="width: 180px; height: auto; margin-bottom: 8px;" />
                        </div>
                        <div class="header-right">
                            <div class="main-title">ATTACHMENT</div>
                            <div class="info-line">ADDRESS {invoice.get('business_address', 'SHASHAMANE')}</div>
                            <div class="info-line">PHONE NUMBER 0975964806/0952930886</div>
                            <div class="info-line">TIN NUMBER 0105581785</div>
                        </div>
                    </div>
                </div>

                <div class="date-section">
                    <span class="date-label">Date</span>
                    <span class="date-underline" style="display: inline-block; width: 160px; border-bottom: 1px solid var(--line-color); margin-left: 5px; vertical-align: bottom; height: 18px;">{invoice.get('sold_at', '')[:10] if invoice.get('sold_at') else ''}</span>
                </div>

                <div class="customer-table">
                    <div class="customer-row">
                        <div class="customer-cell-label">NAME</div>
                        <div class="customer-cell-line">{invoice.get('customer_name', '')}</div>
                    </div>
                    <div class="customer-row">
                        <div class="customer-cell-label">ADDRESS:</div>
                        <div class="customer-cell-line">{invoice.get('customer_region', '')}</div>
                    </div>
                    <div class="customer-row">
                        <div class="customer-cell-label">TIN NO:</div>
                        <div class="customer-cell-line">{invoice.get('customer_id_number', '')}</div>
                    </div>
                </div>

                <table class="data-table">
                    <thead>
                        <tr>
                            <th class="col-desc">DESCRIPTION</th>
                            <th class="col-qty">QTY.</th>
                            <th class="col-price">UNIT PRICE</th>
                            <th class="col-total">TOTAL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {motor_rows if motor_rows else '<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr><tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr><tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr><tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr><tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>'}
                    </tbody>
                </table>

                <div class="footer-table">
                    <div class="footer-row">
                        <div class="footer-left">
                            <div class="payment-box">
                                <div class="payment-row">
                                    <div class="payment-label">PAYMENT METHOD:</div>
                                    <div class="payment-line">{invoice.get('payment_method', '')}</div>
                                </div>
                            </div>
                        </div>
                        <div class="footer-right">
                            <div class="totals-table">
                                <div class="totals-row">
                                    <div class="totals-label-cell">SUB-TOTAL:</div>
                                    <div class="totals-line-cell">{subtotal:,.2f}</div>
                                </div>
                                <div class="totals-row">
                                    <div class="totals-label-cell">DISCOUNT:</div>
                                    <div class="totals-line-cell">{discount:,.2f}</div>
                                </div>
                                <div class="totals-row">
                                    <div class="totals-label-cell">VAT 15%:</div>
                                    <div class="totals-line-cell">{vat:,.2f}</div>
                                </div>
                                <div class="totals-row">
                                    <div class="totals-label-cell">TOTAL:</div>
                                    <div class="totals-line-cell">{total:,.2f}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="signatures-container">
                    <div class="sig-block">
                        <div class="sig-line"></div>
                        <span class="sig-label">SIGNATURE</span>
                    </div>
                    <div class="sig-block">
                        <div class="sig-line"></div>
                        <span class="sig-label">MANAGER</span>
                    </div>
                </div>

            </div>
        </div>

    </body>
    </html>
    """
    
    pdf_path = os.path.join(UPLOAD_DIR, f"{invoice['invoice_id']}.pdf")
    
    HTML(string=html_template).write_pdf(pdf_path)
    
    return f"/uploads/invoices/{invoice['invoice_id']}.pdf"