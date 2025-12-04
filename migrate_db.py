"""
数据库迁移脚本：添加 school_type 字段
如果数据库已存在但没有 school_type 字段，运行此脚本添加
"""
from app import app, db
from models import School
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        try:
            # 检查 school_type 列是否存在
            result = db.session.execute(text("PRAGMA table_info(school)"))
            columns = [row[1] for row in result]
            
            if 'school_type' not in columns:
                print("添加 school_type 字段...")
                # 添加 school_type 列，默认值为 'university'
                db.session.execute(text("""
                    ALTER TABLE school 
                    ADD COLUMN school_type VARCHAR(20) DEFAULT 'university'
                """))
                
                # 更新现有记录，如果没有 school_type 值，设置为 'university'
                db.session.execute(text("""
                    UPDATE school 
                    SET school_type = 'university' 
                    WHERE school_type IS NULL
                """))
                
                db.session.commit()
                print("✓ school_type 字段添加成功！")
                print("  所有现有学校已设置为 'university' 类型")
            else:
                print("✓ school_type 字段已存在，无需迁移")
                
        except Exception as e:
            db.session.rollback()
            print(f"✗ 迁移失败: {e}")
            print("\n如果迁移失败，可以尝试重新初始化数据库：")
            print("  python3 init_db.py")
            return False
    
    return True

if __name__ == '__main__':
    print("开始数据库迁移...")
    if migrate_database():
        print("\n迁移完成！")
    else:
        print("\n迁移失败，请检查错误信息。")

