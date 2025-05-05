from model.db import init_tables
from model.invitation_code import InvitationCode

def init_invitation_codes():
    """初始化邀请码表并生成100个邀请码"""
    print("开始初始化邀请码...")
    
    # 初始化数据库表
    init_tables()
    
    # 创建邀请码模型实例
    inv_code_model = InvitationCode()
    
    # 检查是否已有邀请码
    existing_codes = inv_code_model.find()
    if existing_codes:
        print(f"已存在 {len(existing_codes)} 个邀请码，跳过生成")
        return
    
    # 生成100个新邀请码
    print("生成100个新邀请码...")
    codes = InvitationCode.generate_batch(100)
    inv_code_model.add_all(codes)
    
    print("邀请码生成完成！")
    print("以下是前5个邀请码（用于测试）：")
    for i, code_data in enumerate(codes[:5]):
        print(f"{i+1}. {code_data['code']}")

if __name__ == "__main__":
    init_invitation_codes() 