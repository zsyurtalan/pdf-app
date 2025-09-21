from app import app, db

# Uygulama context'i ile tabloları oluştur
with app.app_context():
    # Tüm tabloları oluştur
    db.create_all()
    print("✅ Tüm tablolar başarıyla oluşturuldu!")
    
    # Tabloları kontrol et
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print("\n📋 Oluşturulan tablolar:")
    for table in tables:
        print(f"  - {table}")
        
        # Her tablonun sütunlarını göster
        columns = inspector.get_columns(table)
        print(f"    Sütunlar:")
        for col in columns:
            print(f"      • {col['name']} ({col['type']})")
        print()
