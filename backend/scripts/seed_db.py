import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import SessionLocal, engine
from app.models import schema

def reset_and_seed_db():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'navcare.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted old database at {db_path}")

    # Create tables via ORM
    schema.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    db.query(schema.EdgeDB).delete()
    db.query(schema.NodeDB).delete()
    db.commit()

    nodes_data = [
        # GROUND FLOOR
        schema.NodeDB(id='d_main_entrance', x=512, y=470, floor=1, is_room=True, name='Main Entrance', name_hi='मुख्य द्वार', keywords='entrance, gate'),
        schema.NodeDB(id='n_hall_g_mid', x=512, y=270, floor=1, is_room=False, name=None, name_hi=None, keywords=None),
        schema.NodeDB(id='d_reception', x=450, y=350, floor=1, is_room=True, name='Reception / Inquiry', name_hi='रिसेप्शन', keywords='reception, help, desk'),
        schema.NodeDB(id='n_hall_g_left', x=150, y=270, floor=1, is_room=False, name=None, name_hi=None, keywords=None),
        schema.NodeDB(id='d_general_opd', x=150, y=170, floor=1, is_room=True, name='General OPD', name_hi='जनरल ओपीडी', keywords='doctor, opd, checkup'),
        schema.NodeDB(id='d_pathology', x=512, y=170, floor=1, is_room=True, name='Pathology Lab', name_hi='पैथोलॉजी', keywords='blood, test, pathology, lab'),
        schema.NodeDB(id='n_hall_g_right', x=800, y=270, floor=1, is_room=False, name=None, name_hi=None, keywords=None),
        schema.NodeDB(id='d_blood_bank', x=800, y=170, floor=1, is_room=True, name='Blood Bank', name_hi='ब्लड बैंक', keywords='blood, donate, bank'),
        schema.NodeDB(id='n_stairs_g', x=800, y=340, floor=1, is_room=True, name='Stairs to First Floor', name_hi='सीढ़ियाँ', keywords='stairs, up'),
        
        # FIRST FLOOR
        schema.NodeDB(id='n_stairs_1', x=110, y=289, floor=2, is_room=True, name='Stairs to Ground Floor', name_hi='सीढ़ियाँ', keywords='stairs, down'),
        schema.NodeDB(id='n_hall_1_left', x=200, y=289, floor=2, is_room=False, name=None, name_hi=None, keywords=None),
        schema.NodeDB(id='d_icu', x=200, y=179, floor=2, is_room=True, name='ICU', name_hi='आईसीयू', keywords='icu, intensive, care'),
        schema.NodeDB(id='n_hall_1_mid', x=300, y=289, floor=2, is_room=False, name=None, name_hi=None, keywords=None),
        schema.NodeDB(id='d_male_ward', x=300, y=409, floor=2, is_room=True, name='General Male Ward', name_hi='पुरुष वार्ड', keywords='ward, male, bed'),
        schema.NodeDB(id='n_hall_1_right', x=580, y=289, floor=2, is_room=False, name=None, name_hi=None, keywords=None),
        schema.NodeDB(id='d_labour', x=580, y=179, floor=2, is_room=True, name='Labour Room', name_hi='लेबर रूम', keywords='labour, delivery, baby'),
    ]

    for node in nodes_data:
        db.add(node)
    
    db.commit()

    edges_data = [
        # Ground Floor Corridors & Rooms
        schema.EdgeDB(from_id='d_main_entrance', to_id='d_reception', distance=50),
        schema.EdgeDB(from_id='d_reception', to_id='d_main_entrance', distance=50),

        schema.EdgeDB(from_id='d_main_entrance', to_id='n_hall_g_mid', distance=200),
        schema.EdgeDB(from_id='n_hall_g_mid', to_id='d_main_entrance', distance=200),

        schema.EdgeDB(from_id='n_hall_g_mid', to_id='d_pathology', distance=100),
        schema.EdgeDB(from_id='d_pathology', to_id='n_hall_g_mid', distance=100),

        schema.EdgeDB(from_id='n_hall_g_mid', to_id='n_hall_g_left', distance=350),
        schema.EdgeDB(from_id='n_hall_g_left', to_id='n_hall_g_mid', distance=350),

        schema.EdgeDB(from_id='n_hall_g_left', to_id='d_general_opd', distance=100),
        schema.EdgeDB(from_id='d_general_opd', to_id='n_hall_g_left', distance=100),

        schema.EdgeDB(from_id='n_hall_g_mid', to_id='n_hall_g_right', distance=300),
        schema.EdgeDB(from_id='n_hall_g_right', to_id='n_hall_g_mid', distance=300),

        schema.EdgeDB(from_id='n_hall_g_right', to_id='d_blood_bank', distance=100),
        schema.EdgeDB(from_id='d_blood_bank', to_id='n_hall_g_right', distance=100),

        schema.EdgeDB(from_id='n_hall_g_right', to_id='n_stairs_g', distance=100),
        schema.EdgeDB(from_id='n_stairs_g', to_id='n_hall_g_right', distance=100),

        # Stairs (Vertical Transition)
        schema.EdgeDB(from_id='n_stairs_g', to_id='n_stairs_1', distance=300),
        schema.EdgeDB(from_id='n_stairs_1', to_id='n_stairs_g', distance=300),

        # First Floor Corridors & Rooms
        schema.EdgeDB(from_id='n_stairs_1', to_id='n_hall_1_left', distance=90),
        schema.EdgeDB(from_id='n_hall_1_left', to_id='n_stairs_1', distance=90),

        schema.EdgeDB(from_id='n_hall_1_left', to_id='d_icu', distance=110),
        schema.EdgeDB(from_id='d_icu', to_id='n_hall_1_left', distance=110),

        schema.EdgeDB(from_id='n_hall_1_left', to_id='n_hall_1_mid', distance=100),
        schema.EdgeDB(from_id='n_hall_1_mid', to_id='n_hall_1_left', distance=100),

        schema.EdgeDB(from_id='n_hall_1_mid', to_id='d_male_ward', distance=120),
        schema.EdgeDB(from_id='d_male_ward', to_id='n_hall_1_mid', distance=120),

        schema.EdgeDB(from_id='n_hall_1_mid', to_id='n_hall_1_right', distance=280),
        schema.EdgeDB(from_id='n_hall_1_right', to_id='n_hall_1_mid', distance=280),

        schema.EdgeDB(from_id='n_hall_1_right', to_id='d_labour', distance=110),
        schema.EdgeDB(from_id='d_labour', to_id='n_hall_1_right', distance=110),
    ]

    for edge in edges_data:
        db.add(edge)

    db.commit()
    db.close()
    print("Database ORM seeded successfully with REAL map coordinates!")

if __name__ == "__main__":
    reset_and_seed_db()
