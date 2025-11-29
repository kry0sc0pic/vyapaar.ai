import odoorpc
import random
import time
import datetime

# ================= CONFIGURATION =================
HOST = 'localhost'
PORT = 8069
DB = 'odoo_pos'
USER = 'admin'
PWD = 'password'

PRODUCTS_DATA = [
    {'name': 'Mother Dairy Full Cream', 'local': 'Mother Dairy Doodh', 'cat': 'Dairy',  'price': 66.00},
    {'name': 'Amul Taaza Milk',         'local': 'Amul Doodh',         'cat': 'Dairy',  'price': 54.00},
    {'name': 'Farm Fresh Eggs',         'local': 'Ande',               'cat': 'Dairy',  'price': 84.00},
    {'name': 'Amul Butter',             'local': 'Makhan',             'cat': 'Dairy',  'price': 58.00},
    {'name': 'Harvest Gold Bread',      'local': 'Bread',              'cat': 'Bakery', 'price': 45.00},
]

print(f"Connecting to Odoo at {HOST}:{PORT}...")
try:
    odoo = odoorpc.ODOO(HOST, port=PORT)
    odoo.login(DB, USER, PWD)
    print("Logged in successfully.")
except Exception as e:
    print(f"Connection Failed: {e}")
    exit()

# Models
PosSession = odoo.env['pos.session']
PosConfig = odoo.env['pos.config']
Sequence = odoo.env['ir.sequence']
PosOrder = odoo.env['pos.order']
Product = odoo.env['product.product']
PosCategory = odoo.env['pos.category']
StockPickingType = odoo.env['stock.picking.type'] # Added Model

print("\n--- STEP 1: PURGING POISONED SESSIONS ---")

# Find ANY session that is not closed
old_sessions = PosSession.search([('state', '!=', 'closed')])

if old_sessions:
    print(f"Found {len(old_sessions)} stuck sessions. Closing them...")
    for sid in old_sessions:
        try:
            # We try to force write the state to closed
            PosSession.write([sid], {'state': 'closed'})
            print(f"-> Force Closed Session {sid}")
        except Exception as e:
            print(f"(!) Could not auto-close Session {sid}. PLEASE CLOSE IT IN THE BROWSER.")
            print(f"    Error: {e}")

print("\n--- STEP 2: VERIFYING SETUP ---")

product_ids_map = []
cat_map = {}

for p in PRODUCTS_DATA:
    if p['cat'] not in cat_map:
        c_id = PosCategory.search([('name', '=', p['cat'])])
        if not c_id:
            c_id = [PosCategory.create({'name': p['cat']})]
        cat_map[p['cat']] = c_id[0]

for p in PRODUCTS_DATA:
    p_id = Product.search([('name', '=', p['name'])])
    if not p_id:
        p_id = [Product.create({
            'name': p['name'], 'default_code': p['local'], 
            'pos_categ_id': cat_map[p['cat']], 'list_price': p['price'],
            'available_in_pos': True
        })]
    product_ids_map.append({'id': p_id[0], 'price': p['price'], 'name': p['name']})

conf_ids = PosConfig.search([], limit=1)
if not conf_ids:
    print("CRITICAL: No POS Configuration found. Please install Point of Sale in Odoo first.")
    exit()

conf = PosConfig.browse(conf_ids[0])

# Fix Main POS Sequence
if not conf.sequence_id:
    print("(!) Config missing sequence. Creating...")
    new_seq = Sequence.create({
        'name': f"POS Sequence {conf.name}", 'padding': 5,
        'prefix': "POS/", 'code': "pos.order", 'company_id': 1
    })
    PosConfig.write([conf.id], {'sequence_id': new_seq})
    print("-> Fixed Sequence.")

if conf.picking_type_id:
    # Check if the picking type has a sequence
    if not conf.picking_type_id.sequence_id:
        print(f"(!) Picking Type '{conf.picking_type_id.name}' missing sequence. Creating...")
        
        pt_seq = Sequence.create({
            'name': f"Picking Sequence {conf.picking_type_id.name}", 
            'padding': 5,
            'prefix': "WH/POS/", 
            'code': "stock.picking", 
            'company_id': 1
        })
        
        # Assign the new sequence to the Picking Type
        StockPickingType.write([conf.picking_type_id.id], {'sequence_id': pt_seq})
        print("-> Fixed Picking Type Sequence.")

print("\n--- STEP 3: CREATING FRESH SESSION ---")

try:
    session_id = PosSession.create({'config_id': conf.id})
    print(f"SUCCESS: Created New Session ID: {session_id}")
    print("-> Please go to Odoo > POS > and click 'Resume' on this new session.")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    print("Likely cause: The old session is still open in the DB.")
    print("Action: Go to Odoo Browser, Close the old session manually, then run this again.")
    exit()

print("\n--- STARTING LIVE INJECTION ---")
print("Press Ctrl+C to stop.")

while True:
    try:
        lines = []
        total_amt = 0.0
        num_items = random.randint(1, 3)
        
        for _ in range(num_items):
            prod = random.choice(product_ids_map)
            qty = random.randint(1, 2)
            line_total = prod['price'] * qty
            total_amt += line_total
            
            lines.append((0, 0, {
                'product_id': prod['id'],
                'qty': qty,
                'price_unit': prod['price'],
                'price_subtotal': line_total,
                'price_subtotal_incl': line_total,
            }))

        order_vals = {
            'name': f"LIVE/{random.randint(10000,99999)}",
            'session_id': session_id,
            'date_order': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'pos_reference': f"Ref-{random.randint(10000,99999)}",
            'lines': lines,
            'amount_total': total_amt,
            'amount_tax': 0,
            'amount_paid': total_amt,
            'amount_return': 0,
            'state': 'paid',
        }

        new_order_id = PosOrder.create(order_vals)
        print(f"[Success] Order {new_order_id} | Total: {total_amt}")
        time.sleep(random.randint(2, 5))

    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
