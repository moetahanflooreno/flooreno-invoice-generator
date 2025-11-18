import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import datetime
import io

# --- Constants ---
TAX_RATE = 0.13 # 13% Tax

# ---------- PDF CREATION (Updated Table Layout and Summary) ----------
def create_invoice_pdf(client_name, phone, items, payment_type, subtotal, tax, total, location, cash_given=None, change=None):
    """Generates the PDF document for the invoice with a clean, customer-friendly table layout."""
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title and store info
    elements.append(Paragraph("<b>Flooreno Store Invoice</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Store Location:</b> {location}", styles["Normal"]))
    elements.append(Spacer(1, 6))

    # Client and Transaction Info
    client_info = f"""
    <b>Customer Name:</b> {client_name}<br/>
    <b>Phone Number:</b> {phone}<br/>
    <b>Date:</b> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br/>
    <b>Payment Type:</b> {payment_type}<br/>
    """
    if payment_type == "Cash" and cash_given is not None and change is not None:
        client_info += f"<b>Cash Given:</b> ${cash_given:.2f}<br/><b>Change:</b> ${change:.2f}<br/>"
    
    elements.append(Paragraph(client_info, styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Items Table (Updated columns for Qty, Line Total Pre-Tax, and Line Total Post-Tax)
    # Changed header of the last column to be clearer.
# --- Styles for wrapped text and smaller fonts ---
    small_style = styles["Normal"]
    small_style.fontSize = 8
    small_style.leading = 10

    # Items Table (Updated columns with wrapping and smaller text)
    data = [[
        Paragraph("<b>Item Description</b>", small_style),
        Paragraph("<b>Unit Price</b>", small_style),
        Paragraph("<b>Qty</b>", small_style),
        Paragraph("<b>SubTotal</b>", small_style),
        Paragraph(f"<b>Total</b>", small_style)
    ]]

    # Populate items (with wrapped descriptions)
    for item, price, quantity in items:
        line_total_pre_tax = price * quantity
        line_total_post_tax = line_total_pre_tax * (1 + TAX_RATE)

        data.append([
            Paragraph(item, small_style),   # WRAPPED TEXT
            Paragraph(f"{price:.2f}", small_style),
            Paragraph(str(quantity), small_style),
            Paragraph(f"{line_total_pre_tax:.2f}", small_style),
            Paragraph(f"{line_total_post_tax:.2f}", small_style)
        ])

    # Summary rows
    data.append(["", "", "", Paragraph("Subtotal", small_style), Paragraph(f"{subtotal:.2f}", small_style)])
    data.append(["", "", "", Paragraph(f"Tax ({TAX_RATE*100:.0f}%)", small_style), Paragraph(f"{tax:.2f}", small_style)])
    data.append(["", "", "", Paragraph("<b>TOTAL</b>", small_style), Paragraph(f"<b>{total:.2f}</b>", small_style)])

    # Enlarged table width for better spacing
    table = Table(data, colWidths=[220, 60, 40, 70, 80])

    item_count = len(items)
    grid_end_row = item_count

    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Smaller font
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Allow wrapping

        ('INNERGRID', (0, 0), (-1, grid_end_row), 0.25, colors.black),
        ('BOX', (0, 0), (-1, grid_end_row), 0.25, colors.black),

        ('SPAN', (0, -3), (2, -3)),
        ('SPAN', (0, -2), (2, -2)),
        ('SPAN', (0, -1), (2, -1)),

        ('LINEABOVE', (3, -3), (4, -3), 0.5, colors.black),

        ('FONTNAME', (3, -1), (4, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (3, -1), (4, -1), colors.lightgrey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Thank you for shopping at Flooreno!", styles["Italic"]))
    
    pdf.build(elements)
    buffer.seek(0)
    return buffer

# --- Helper Function for Dynamic Totals ---
def calculate_totals(items):
    """Calculates subtotal, tax, and total from the item list."""
    subtotal = sum(price * quantity for _, price, quantity in items)
    tax = subtotal * TAX_RATE
    total = subtotal + tax
    return subtotal, tax, total

# --- Callback Function to Add Item and Reset Inputs Safely ---
def add_item_and_reset():
    """Adds the current input item to the list and resets input fields using session state keys."""
    name = st.session_state.temp_name.strip()
    price = st.session_state.temp_price
    quantity = st.session_state.temp_qty

    if name and price > 0 and quantity > 0:
        # 1. Add item to the list
        st.session_state.invoice_items.append((name, price, quantity))
        # 2. Set success message
        st.session_state.message = {"type": "success", "text": f"Added {quantity} x {name} @ ${price:.2f}"}
        
        # 3. SAFELY RESET INPUTS (Executed before the next script rerun)
        st.session_state.temp_name = ""
        st.session_state.temp_price = 0.0
        st.session_state.temp_qty = 1 
    else:
        # 4. Set error message
        st.session_state.message = {"type": "error", "text": "Please ensure item name, price, and quantity are valid."}


# ---------- STREAMLIT APP ----------
st.set_page_config(layout="wide")
st.title("🧾 Flooreno Invoice Generator")

# Session initialization and transient message setup
if "invoice_items" not in st.session_state:
    st.session_state.invoice_items = []
if 'message' not in st.session_state:
    st.session_state.message = {"type": None, "text": None}
if 'temp_name' not in st.session_state: st.session_state.temp_name = ""
if 'temp_price' not in st.session_state: st.session_state.temp_price = 0.0
if 'temp_qty' not in st.session_state: st.session_state.temp_qty = 1

# Display message from previous click event
if st.session_state.message['type'] == 'success':
    st.success(st.session_state.message['text'])
    st.session_state.message = {"type": None, "text": None} # Clear message after display
elif st.session_state.message['type'] == 'error':
    st.error(st.session_state.message['text'])
    st.session_state.message = {"type": None, "text": None} # Clear message after display

# --- 1. Location Dropdown ---
st.markdown("### Store and Customer Details")
location = st.selectbox(
    "Select Store Location:", 
    ["NY", "Sauga", "Dragona", "Ottawa"],
    key="location_select"
)

col_name, col_phone = st.columns(2)
client_name = col_name.text_input("Client Name")
phone = col_phone.text_input("Phone Number")


st.markdown("---")
st.write("### Add New Item")

# --- 2. Item Input with Columns for Price and Quantity ---
col_desc, col_price_in, col_qty_in, col_add_btn = st.columns([4, 2, 2, 1])

# Input fields bound to session state keys
temp_item_name = col_desc.text_input(
    "Item Description / Number", 
    key="temp_name", 
    label_visibility="visible"
)
temp_price = col_price_in.number_input(
    "Unit Price ($)", 
    min_value=0.0, 
    step=0.01, 
    key="temp_price", 
    format="%.2f", 
    label_visibility="visible"
)
temp_quantity = col_qty_in.number_input(
    "Quantity", 
    min_value=1, 
    step=1, 
    key="temp_qty", 
    label_visibility="visible"
)

# Add item button uses the callback function
with col_add_btn:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    st.button(
        "➕ Add",
        key="add_item_btn",
        use_container_width=True,
        on_click=add_item_and_reset
    )


st.markdown("---")

# --- Calculate Totals and Display Item Table ---

# Calculate totals dynamically
subtotal, tax, total = calculate_totals(st.session_state.invoice_items)

st.write("### Current Items ")

if st.session_state.invoice_items:
    # Header row for the editable list
    # [Description, Price, Qty, Line Total Pre-Tax, Line Total Post-Tax, Remove]
    header_cols = st.columns([3, 1.5, 1, 1.5, 1.5, 1])
    header_cols[0].markdown("**Description**")
    header_cols[1].markdown("**Unit Price ($)**")
    header_cols[2].markdown("**Quantity**")
    header_cols[3].markdown("**Total ($)**")
    header_cols[4].markdown(f"**Total After Tax ({TAX_RATE*100:.0f}%)**")

    # Editable list loop
    items_to_keep = []
    
    for i, (name, price, quantity) in enumerate(st.session_state.invoice_items):
        # Columns adjusted to include the new calculated total
        cols = st.columns([3, 1.5, 1, 1.5, 1.5, 1])
        
        # Display Name
        cols[0].write(name)

        # Editable Price (Using unique key)
        new_price = cols[1].number_input(
            "Price",
            min_value=0.0,
            step=0.01,
            value=price,
            key=f"price_{i}",
            label_visibility="collapsed",
            format="%.2f"
        )
        
        # Editable Quantity (Using unique key)
        new_quantity = cols[2].number_input(
            "Quantity",
            min_value=1,
            step=1,
            value=quantity,
            key=f"qty_{i}",
            label_visibility="collapsed"
        )

        # Line Total (Pre-Tax)
        line_total_pre_tax = new_price * new_quantity
        cols[3].write(f"**${line_total_pre_tax:.2f}**")
        
        # Line Total (Post-Tax) - NEW COLUMN
        line_total_with_tax = line_total_pre_tax * (1 + TAX_RATE)
        cols[4].write(f"**${line_total_with_tax:.2f}**")

        # Check for removal
        if cols[5].button("🗑️", key=f"remove_{i}", use_container_width=True):
            # Deletion is handled after the loop
            pass
        else:
            # If not removed, update item details and add to the list to keep
            items_to_keep.append((name, new_price, new_quantity))


    # Update session state after the loop to handle removals correctly
    if len(items_to_keep) != len(st.session_state.invoice_items):
         st.session_state.invoice_items = items_to_keep
         st.rerun()
    elif st.session_state.invoice_items != items_to_keep:
         st.session_state.invoice_items = items_to_keep
         st.rerun()


else:
    st.info("No items added yet.")

st.markdown("---")

# --- 5. Payment and PDF Generation ---
st.markdown(f"#### Total Due: ${total:.2f}")

payment_type = st.selectbox("Payment Type", ["Cash", "Debit", "Credit"])
selected_payment_type = payment_type

cash_given = None
change = None
cash_error_message = None

if selected_payment_type == "Cash":
    # st.markdown(f"#### Total Due: ${total:.2f}")
    cash_given = st.number_input("Cash Given ($)", min_value=0.0, step=0.01, format="%.2f", key="cash_input")
    
    if total > 0:
        if cash_given >= total:
            change = cash_given - total
            st.success(f"Change to return: **${change:.2f}**")
        else:
            cash_error_message = f"Cash given is less than total **${total:.2f}**. Please input sufficient cash."
            st.warning(cash_error_message)


# --- Conditional Validation and Combined Button ---
can_generate_pdf = True
error_messages = []

# Validation 1: Required Fields
if not client_name or not phone or not st.session_state.invoice_items:
    error_messages.append("Client Name, Phone, and at least one item are required.")
    can_generate_pdf = False

# Validation 2: Cash Payment Check
if selected_payment_type == "Cash" and total > 0 and (cash_given is None or cash_given < total):
    error_messages.append("Insufficient cash provided for the total amount.")
    can_generate_pdf = False
    
# Display accumulated errors
for msg in error_messages:
    st.error(msg)
    
# Combined Download Button logic
if can_generate_pdf:
    
    # Logic to create PDF buffer
    pdf_buffer = create_invoice_pdf(
        client_name,
        phone,
        st.session_state.invoice_items,
        selected_payment_type,
        subtotal,
        tax,
        total,
        location,
        cash_given=cash_given,
        change=change
    )
    
    st.balloons()
    
    # Use st.download_button to immediately offer the download
    st.download_button(
        label="✅ Download Invoice PDF",
        data=pdf_buffer,
        file_name=f"Invoice_{client_name.replace(' ', '_')}_{phone}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        type="primary"
    )
    st.success("Invoice PDF has been generated and is ready for download.")

else:
    # Display a disabled button if requirements are not met
    st.button("Download Invoice PDF (Validation Pending)", disabled=True)
