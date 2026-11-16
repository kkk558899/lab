import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.utils.password import hash_password

logger = logging.getLogger(__name__)

# 旧版打包中误填的无效哈希，若已生成库则启动时自动修复
_LEGACY_BROKEN_HASH = "$2b$12$6K8nQ6O5sH0iL6I0r6mSde7N1rN0zU6oE4hM6fP1nO8vV0kP1lQ7e"

DEFAULT_USERS = [
    {
        "id": 1,
        "username": "admin",
        "name": "管理员",
        "role": "admin",
        "email": "admin@lab.com",
        "phone": "13800000001",
        "status": 1
    },
    {
        "id": 2,
        "username": "student",
        "name": "李同学",
        "role": "student",
        "email": "student@lab.com",
        "phone": "13800000002",
        "status": 1
    }
]

DEFAULT_LABS = [
    {"id": 1, "name": "计算机综合实验室", "description": "配备高性能PC主机与双屏显示器，适合算法实训与编程教学", "location": "综合实验楼101", "capacity": 50, "open_time": "08:00", "close_time": "21:00", "status": 1},
    {"id": 2, "name": "电子电路实验室", "description": "配备示度器、信号发生器、稳压电源等基础电路仪器", "location": "综合实验楼201", "capacity": 30, "open_time": "08:30", "close_time": "18:00", "status": 1},
    {"id": 3, "name": "大学物理实验室", "description": "配备光学导轨、氦氖激光器、分光计等物理实验器材", "location": "综合实验楼202", "capacity": 30, "open_time": "08:00", "close_time": "20:00", "status": 1},
    {"id": 4, "name": "化学实验室", "description": "配备通风橱、电子天平、pH计等，化学试剂操作专区", "location": "综合实验楼301", "capacity": 20, "open_time": "08:00", "close_time": "18:00", "status": 1},
    {"id": 5, "name": "生物实验室", "description": "配备高倍显微镜、恒温培养箱、PCR扩增仪等生物器械", "location": "综合实验楼302", "capacity": 20, "open_time": "08:00", "close_time": "18:00", "status": 1},
    {"id": 6, "name": "人工智能实验室", "description": "配备多卡RTX4090算力服务器、工作站与深度相机", "location": "综合实验楼401", "capacity": 30, "open_time": "08:00", "close_time": "18:00", "status": 1},
    {"id": 7, "name": "机器人实验室", "description": "配备UR5机械臂、激光雷达与Orin嵌入式计算平台", "location": "综合实验楼402", "capacity": 20, "open_time": "09:00", "close_time": "17:00", "status": 1},
    {"id": 8, "name": "软件工程实验室", "description": "配备项目协作工作站与CI/CD服务器，软件开发实训专区", "location": "综合实验楼501", "capacity": 40, "open_time": "08:00", "close_time": "20:00", "status": 1}
]

DEFAULT_EQUIPMENTS = [
    {"id": 1,  "lab_id": 1, "name": "RTX4090", "description": "深度学习训练显卡", "spec": "24G 显存", "quantity": 2, "status": 1},
    {"id": 2,  "lab_id": 1, "name": "开发主机", "description": "学生上机编程", "spec": "i7 / 32G / 1T SSD", "quantity": 20, "status": 1},
    {"id": 3,  "lab_id": 1, "name": "投影仪", "description": "讲课演示", "spec": "1080P", "quantity": 1, "status": 1},
    {"id": 4,  "lab_id": 1, "name": "千兆交换机", "description": "机房组网", "spec": "24 口", "quantity": 1, "status": 1},
    {"id": 5,  "lab_id": 2, "name": "示波器", "description": "电路波形观测", "spec": "100MHz 双通道", "quantity": 8, "status": 1},
    {"id": 6,  "lab_id": 2, "name": "信号发生器", "description": "信号源实验", "spec": "DDS 60MHz", "quantity": 6, "status": 1},
    {"id": 7,  "lab_id": 2, "name": "数字万用表", "description": "电子测量", "spec": "4 位半", "quantity": 10, "status": 0},
    {"id": 8,  "lab_id": 2, "name": "直流稳压电源", "description": "电路供电", "spec": "30V 5A", "quantity": 8, "status": 1},
    {"id": 9,  "lab_id": 3, "name": "光学实验台", "description": "几何光学实验", "spec": "1.2m 隔振台", "quantity": 4, "status": 1},
    {"id": 10, "lab_id": 3, "name": "氦氖激光器", "description": "干涉衍射实验", "spec": "632.8nm", "quantity": 2, "status": 1},
    {"id": 11, "lab_id": 3, "name": "力学轨道", "description": "牛顿定律实验", "spec": "气垫导轨 1.5m", "quantity": 3, "status": 1},
    {"id": 12, "lab_id": 3, "name": "分光计", "description": "光谱测量", "spec": "0.1° 精度", "quantity": 4, "status": 1},
    {"id": 13, "lab_id": 4, "name": "电子天平", "description": "试剂称量", "spec": "0.1mg", "quantity": 6, "status": 1},
    {"id": 14, "lab_id": 4, "name": "离心机", "description": "样品分离", "spec": "4000rpm", "quantity": 2, "status": 1},
    {"id": 15, "lab_id": 4, "name": "通风橱", "description": "有机实验", "spec": "1.5m", "quantity": 3, "status": 1},
    {"id": 16, "lab_id": 4, "name": "pH 计", "description": "溶液酸碱度", "spec": "0.01pH", "quantity": 4, "status": 1},
    {"id": 17, "lab_id": 5, "name": "显微镜", "description": "细胞观察", "spec": "1000x 光学", "quantity": 10, "status": 1},
    {"id": 18, "lab_id": 5, "name": "恒温培养箱", "description": "菌种培养", "spec": "室温 ~ 60℃", "quantity": 2, "status": 1},
    {"id": 19, "lab_id": 5, "name": "移液器", "description": "微量取样", "spec": "0.5-10μL", "quantity": 20, "status": 1},
    {"id": 20, "lab_id": 5, "name": "PCR 仪", "description": "基因扩增", "spec": "96 孔", "quantity": 1, "status": 0},
    {"id": 21, "lab_id": 6, "name": "GPU 训练服务器", "description": "大模型微调", "spec": "2 * RTX4090 / 128G", "quantity": 1, "status": 1},
    {"id": 22, "lab_id": 6, "name": "RTX4090", "description": "深度学习训练显卡", "spec": "24G 显存", "quantity": 4, "status": 1},
    {"id": 23, "lab_id": 6, "name": "深度相机", "description": "视觉数据采集", "spec": "RealSense D435i", "quantity": 3, "status": 1},
    {"id": 24, "lab_id": 6, "name": "标注工作站", "description": "数据集标注", "spec": "i9 / 64G", "quantity": 6, "status": 1},
    {"id": 25, "lab_id": 7, "name": "UR5 机械臂", "description": "工业机械臂教学", "spec": "负载 5kg", "quantity": 2, "status": 1},
    {"id": 26, "lab_id": 7, "name": "Livox 激光雷达", "description": "SLAM 建图", "spec": "Mid-360", "quantity": 3, "status": 1},
    {"id": 27, "lab_id": 7, "name": "RealSense 深度相机", "description": "视觉抓取", "spec": "D435i", "quantity": 4, "status": 1},
    {"id": 28, "lab_id": 7, "name": "Jetson Orin", "description": "边缘计算", "spec": "32G", "quantity": 4, "status": 1},
    {"id": 29, "lab_id": 8, "name": "开发主机", "description": "项目实训", "spec": "i7 / 32G / 1T SSD", "quantity": 40, "status": 1},
    {"id": 30, "lab_id": 8, "name": "显示器", "description": "双屏开发", "spec": "27 寸 2K", "quantity": 40, "status": 1},
    {"id": 31, "lab_id": 8, "name": "投影仪", "description": "答辩演示", "spec": "1080P", "quantity": 2, "status": 1},
    {"id": 32, "lab_id": 8, "name": "代码服务器", "description": "Git 与 CI", "spec": "8 核 / 32G", "quantity": 1, "status": 1}
]

def seed_initial_data(db: Session):
    """如果数据库为空（如首次在他人机器运行或使用 SQLite），自动写入基础数据"""
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            logger.info("检测到数据库为空，正在自动播种初始数据...")
            default_pwd_hash = hash_password("123456")
            for u in DEFAULT_USERS:
                db.add(User(**u, password=default_pwd_hash))
            for l in DEFAULT_LABS:
                db.add(Lab(**l))
            for eq in DEFAULT_EQUIPMENTS:
                db.add(Equipment(**eq))
            db.commit()
            logger.info("初始数据播种成功！默认管理员: admin/123456，学生: student/123456")
        else:
            broken_users = db.query(User).filter(User.password == _LEGACY_BROKEN_HASH).all()
            if broken_users:
                valid_hash = hash_password("123456")
                for bu in broken_users:
                    bu.password = valid_hash
                db.commit()
                logger.info(f"已自动修复 {len(broken_users)} 个默认账号的初始密码哈希")
    except Exception as e:
        db.rollback()
        logger.warning(f"自动初始化数据跳过或已存在: {e}")
