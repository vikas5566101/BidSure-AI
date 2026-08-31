from reportlab.pdfgen import canvas

output_path = "mock_data/documents/test_gst_certificate.pdf"

pdf = canvas.Canvas(output_path)

pdf.setFont("Helvetica-Bold", 16)
pdf.drawString(100, 750, "GST REGISTRATION CERTIFICATE")

pdf.setFont("Helvetica", 12)
pdf.drawString(100, 700, "GSTIN: 27ABCDE1234F1Z5")
pdf.drawString(100, 670, "Legal Name: ABC Industries Pvt Ltd")
pdf.drawString(100, 640, "Registration Date: 15/04/2022")
pdf.drawString(100, 610, "Registration Status: Active")
pdf.drawString(100, 580, "Business Type: Private Limited Company")
pdf.drawString(
    100,
    550,
    "Principal Address: 123 Industrial Area, Mumbai, Maharashtra"
)

pdf.save()

print(f"Created: {output_path}")