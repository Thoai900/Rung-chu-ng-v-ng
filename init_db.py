import mysql.connector
import os

def get_db_config():
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'Thoai12345'),
        'database': os.getenv('DB_NAME', 'rung_chuong_vang')
    }

def init_db():
    conn = mysql.connector.connect(**get_db_config())
    cursor = conn.cursor()

    # Create exam_results table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exam_results (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_name VARCHAR(100) NOT NULL,
        class_name VARCHAR(50) NOT NULL,
        score INT NOT NULL,
        total_time INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("Table 'exam_results' created or checked.")

    # Create students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INT AUTO_INCREMENT PRIMARY KEY,
        full_name VARCHAR(100) NOT NULL,
        class_name VARCHAR(50) NOT NULL,
        login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("Table 'students' created or checked.")
    
    # Create questions table 
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        category VARCHAR(100),
        content TEXT NOT NULL,
        options TEXT,
        answer TEXT NOT NULL,
        type VARCHAR(20)
    )
    """)
    print("Table 'questions' created or checked.")

    # Create admins table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(100) UNIQUE NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'editor',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("Table 'admins' created or checked.")

    # Create pending_changes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pending_changes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        admin_id INT,
        action_type VARCHAR(20) NOT NULL,
        question_id INT,
        new_content_json TEXT,
        status VARCHAR(20) DEFAULT 'PENDING',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
    )
    """)
    print("Table 'pending_changes' created or checked.")

    # Insert a guaranteed Super Admin for testing (if not exists)
    # Replace with your actual email if needed
    cursor.execute("INSERT IGNORE INTO admins (email, role) VALUES ('admin@example.com', 'super_admin')")
    
    # Clear existing questions to avoid duplicates for this setup
    cursor.execute("TRUNCATE TABLE questions")

    # DATASET
    # Format: (category, content, options, answer, type)
    # type: 'trac_nghiem' OR 'tu_luan'
    
    questions = [
        # --- 1. PHONG TỤC NGÀY TẾT ---
        # Trắc nghiệm (1-5)
        ('Phong tục ngày Tết', "Tên gọi khác của Tết Nguyên Đán là gì?", "A. Tết Tây; B. Tết Âm lịch; C. Tết Đoan Ngọ; D. Tết Trung Thu", "B. Tết Âm lịch", "trac_nghiem"),
        ('Phong tục ngày Tết', "Hoạt động tiễn đưa các vị thần về trời vào ngày 23 tháng Chạp gọi là gì?", "A. Tiễn ông Tơ bà Nguyệt; B. Tiễn Thần Tài; C. Tiễn ông Công ông Táo; D. Tiễn Thổ Địa", "C. Tiễn ông Công ông Táo", "trac_nghiem"),
        ('Phong tục ngày Tết', "'Xông đất' là gì?", "A. Người đầu tiên vào nhà sau giao thừa; B. Quét dọn đất đai; C. Đi mua đất đầu năm; D. Đắp đất vào gốc cây", "A. Người đầu tiên vào nhà sau giao thừa", "trac_nghiem"),
        ('Phong tục ngày Tết', "Theo quan niệm dân gian, người ta thường mua gì đầu năm để cầu may mắn?", "A. Mua vôi; B. Mua muối; C. Mua lửa; D. Mua gạo", "B. Mua muối", "trac_nghiem"),
        ('Phong tục ngày Tết', "Hoạt động đi thăm viếng mộ tổ tiên trước Tết gọi là gì?", "A. Tảo mộ; B. Chạp mả; C. Viếng lăng; D. Đắp mộ", "A. Tảo mộ", "trac_nghiem"),
        # Tự luận (6-10)
        ('Phong tục ngày Tết', "Người Việt thường thắp hương theo số lẻ hay số chẵn?", "", "Số lẻ", "tu_luan"),
        ('Phong tục ngày Tết', "Tục lệ chúc thọ người già và tặng tiền cho trẻ em vào đầu năm gọi là gì?", "", "Lì xì", "tu_luan"),
        ('Phong tục ngày Tết', "Để xua đuổi quỷ dữ theo truyền thuyết, người ta thường dựng cây gì trước sân nhà?", "", "Cây Nêu", "tu_luan"),
        ('Phong tục ngày Tết', "Nghi lễ tạ ơn trời đất, tổ tiên được thực hiện ngay thời điểm chuyển giao năm cũ và năm mới là gì?", "", "Cúng Giao thừa", "tu_luan"),
        ('Phong tục ngày Tết', "Tại sao người ta kiêng quét nhà vào mùng 1 Tết?", "", "Sợ quét mất tài lộc", "tu_luan"),

        # --- 2. Ý NGHĨA CÁC MÓN ĂN ---
        # Trắc nghiệm
        ('Ý nghĩa các món ăn', "Bánh chưng có hình vuông tượng trưng cho điều gì?", "A. Trời; B. Mặt đất; C. Vũ trụ; D. Con người", "B. Mặt đất", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "Loại gạo nào là nguyên liệu chính để làm bánh chưng, bánh tét?", "A. Gạo tẻ; B. Gạo nếp; C. Gạo lứt; D. Gạo tấm", "B. Gạo nếp", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "Món ăn làm từ thịt lợn, màu trong suốt, ăn kèm dưa hành ở miền Bắc?", "A. Giò thủ; B. Thịt đông; C. Chả quế; D. Nem chua", "B. Thịt đông", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "Mâm ngũ quả miền Nam: Mãng cầu, Dừa, Đu đủ, Xoài và quả gì để thành 'Cầu vừa đủ xài'?", "A. Sung; B. Thơm; C. Quất; D. Chuối", "A. Sung", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "Loại quả nào thường có trên mâm ngũ quả miền Bắc, trông như bàn tay Phật?", "A. Chuối; B. Phật thủ; C. Bưởi; D. Cam", "B. Phật thủ", "trac_nghiem"),
        # Tự luận
        ('Ý nghĩa các món ăn', "Món 'Khổ qua nhồi thịt' được ăn ngày Tết với ý nghĩa gì?", "", "Mong nỗi khổ qua đi", "tu_luan"),
        ('Ý nghĩa các món ăn', "Hạt của loại quả nào thường được nhuộm đỏ, tượng trưng cho may mắn trong khay mứt Tết?", "", "Hạt dưa", "tu_luan"),
        ('Ý nghĩa các món ăn', "Bánh Tét là đặc sản của miền nào trong dịp Tết?", "", "Miền Nam", "tu_luan"),
        ('Ý nghĩa các món ăn', "Loại củ nào thường được ngâm chua ngọt để ăn kèm thịt kho tàu hoặc bánh chưng?", "", "Củ kiệu", "tu_luan"),
        ('Ý nghĩa các món ăn', "Tại sao trên mâm ngũ quả miền Bắc thường có nải chuối xanh?", "", "Tượng trưng bàn tay che chở", "tu_luan"),

        # --- 3. LOÀI HOA ---
        # Trắc nghiệm
        ('Loài hoa', "Loài hoa đặc trưng cho Tết miền Bắc là hoa gì?", "A. Hoa Mai; B. Hoa Đào; C. Hoa Lan; D. Hoa Cúc", "B. Hoa Đào", "trac_nghiem"),
        ('Loài hoa', "Loài hoa đặc trưng cho Tết miền Nam là hoa gì?", "A. Hoa Mai; B. Hoa Đào; C. Hoa Hồng; D. Hoa Ly", "A. Hoa Mai", "trac_nghiem"),
        ('Loài hoa', "Hoa Mai thường có mấy cánh thì được coi là rất may mắn?", "A. 4 cánh; B. 5 cánh; C. 6 cánh; D. 8 hoặc 10 cánh", "D. 8 hoặc 10 cánh", "trac_nghiem"),
        ('Loài hoa', "Loài hoa màu vàng rực, tên gọi gợi nhớ đến sự trường thọ?", "A. Hướng Dương; B. Cúc Vạn Thọ; C. Hoa Ly; D. Hoa Huệ", "B. Cúc Vạn Thọ", "trac_nghiem"),
        ('Loài hoa', "Cây quất (tắc) trĩu quả tượng trưng cho điều gì?", "A. Tình yêu; B. Sự sung túc, tài lộc; C. Sức khỏe; D. Trí tuệ", "B. Sự sung túc, tài lộc", "trac_nghiem"),
        # Tự luận
        ('Loài hoa', "Hoa Đào có màu đỏ thắm được gọi là đào gì?", "", "Đào Bích", "tu_luan"),
        ('Loài hoa', "Loài hoa có tên gợi nhớ giàu sang, thường chơi trong bình nước?", "", "Hoa Thủy Tiên", "tu_luan"),
        ('Loài hoa', "Hoa Đào thường được coi là biểu tượng để xua đuổi vật gì theo truyền thuyết?", "", "Ma quỷ", "tu_luan"),
        ('Loài hoa', "Ngoài hoa Mai vàng, miền Nam còn có loài hoa 'Tứ quý' nở quanh năm là gì?", "", "Mai tứ quý", "tu_luan"),
        ('Loài hoa', "Hoa có màu đỏ rực, hình dáng giống chiếc mào con gà?", "", "Hoa Mào Gà", "tu_luan"),

        # --- 4. NGÀY TẾT TRONG VĂN HỌC ---
        # Trắc nghiệm
        ('Ngày tết trong văn học', "Câu 'Thịt mỡ, dưa hành, câu đối đỏ...' thuộc thể loại nào?", "A. Thơ tự do; B. Câu đối dân gian; C. Vè; D. Ca dao", "B. Câu đối dân gian", "trac_nghiem"),
        ('Ngày tết trong văn học', "Trong bài thơ 'Ông Đồ', ông đồ thường xuất hiện khi nào?", "A. Khi hoa mai nở; B. Khi hoa đào nở; C. Khi trời mưa phùn; D. Khi hè về", "B. Khi hoa đào nở", "trac_nghiem"),
        ('Ngày tết trong văn học', "Nhà thơ nào có bài 'Tết của mẹ tôi'?", "A. Xuân Diệu; B. Huy Cận; C. Nguyễn Bính; D. Tố Hữu", "C. Nguyễn Bính", "trac_nghiem"),
        ('Ngày tết trong văn học', "Trong truyện 'Bánh chưng bánh giầy', ai tạo ra hai loại bánh này?", "A. Sơn Tinh; B. Lang Liêu; C. Thánh Gióng; D. An Dương Vương", "B. Lang Liêu", "trac_nghiem"),
        ('Ngày tết trong văn học', "'Xuân tóc đỏ' là nhân vật trong tiểu thuyết nào?", "A. Tắt đèn; B. Chí Phèo; C. Số Đỏ; D. Vợ Nhặt", "C. Số Đỏ", "trac_nghiem"),
        # Tự luận
        ('Ngày tết trong văn học', "Điền từ: 'Cung chúc tân xuân / ... vạn sự như ý'.", "", "Vạn sự", "tu_luan"),
        ('Ngày tết trong văn học', "Tác phẩm 'Sống mòn' của Nam Cao có nhắc đến không khí Tết buồn bã đúng hay sai?", "", "Đúng", "tu_luan"),
        ('Ngày tết trong văn học', "Trong thơ Đoàn Văn Cừ, ông thường tả cảnh gì đặc trưng ở quê?", "", "Chợ Tết", "tu_luan"),
        ('Ngày tết trong văn học', "Ai nói: 'Mùa xuân là Tết trồng cây / Làm cho đất nước càng ngày càng xuân'?", "", "Chủ tịch Hồ Chí Minh", "tu_luan"),
        ('Ngày tết trong văn học', "Tập thơ nổi tiếng của Xuân Diệu tên là gì?", "", "Thơ thơ", "tu_luan"),

        # --- 5. CA DAO ---
        # Trắc nghiệm
        ('Ca dao', "Số cô chẳng giàu thì nghèo, Ngày ba mươi Tết có ... treo trong nhà?", "A. Bánh chưng; B. Thịt; C. Tranh; D. Đèn", "B. Thịt", "trac_nghiem"),
        ('Ca dao', "Mùng một Tết cha, mùng hai Tết mẹ, mùng ba Tết ...?", "A. Vợ; B. Con; C. Thầy; D. Bạn", "C. Thầy", "trac_nghiem"),
        ('Ca dao', "Thịt mỡ dưa hành câu đối đỏ - ... tràng pháo bánh chưng xanh?", "A. Hoa đào; B. Cây nêu; C. Mứt gừng; D. Rượu nếp", "B. Cây nêu", "trac_nghiem"),
        ('Ca dao', "Dù ai đi ngược về xuôi, Nhớ ngày ... giỗ Tổ mùng mười tháng ba?", "A. Hội Lim; B. Giỗ Tổ; C. Lễ chùa; D. Về quê", "B. Giỗ Tổ", "trac_nghiem"),
        ('Ca dao', "Ba mươi chưa phải là ...?", "A. Cuối tháng; B. Tết; C. Hết tiền; D. Mùa xuân", "B. Tết", "trac_nghiem"),
        # Tự luận
        ('Ca dao', "Hoàn thành: 'Tháng Giêng là tháng ăn chơi, Tháng Hai trồng đậu, trồng khoai, ...'", "", "Trồng cà", "tu_luan"),
        ('Ca dao', "Điền từ: 'Hễ cứ hoa đào nở, Là ... lại về'.", "", "Tết", "tu_luan"),
        ('Ca dao', "Đầu năm mua muối, cuối năm mua ...", "", "Vôi", "tu_luan"),
        ('Ca dao', "Cu kêu ba tiếng cu kêu, Cho mau tới Tết dựng nêu ...", "", "Ăn chè", "tu_luan"),
        ('Ca dao', "Có rau có cháo cũng xong, Miễn là có cái ... trong ngày xuân", "", "Bánh chưng", "tu_luan"),

        # --- 6. KIẾN THỨC XÃ HỘI ---
        # Trắc nghiệm
        ('Kiến thức xã hội', "Năm 2026 theo âm lịch là năm con gì?", "A. Giáp Thìn; B. Bính Ngọ (Ngựa); C. Ất Tỵ; D. Đinh Mùi", "B. Bính Ngọ (Ngựa)", "trac_nghiem"),
        ('Kiến thức xã hội', "Quốc gia nào ngoài VN cũng ăn Tết Âm lịch?", "A. Nhật Bản; B. Trung Quốc; C. Thái Lan; D. Lào", "B. Trung Quốc", "trac_nghiem"),
        ('Kiến thức xã hội', "Tết Nguyên Tiêu là ngày nào?", "A. Rằm tháng Giêng; B. Rằm tháng Bảy; C. Mùng 10 tháng Giêng; D. Rằm tháng Tám", "A. Rằm tháng Giêng", "trac_nghiem"),
        ('Kiến thức xã hội', "Tổng thống Mỹ có thường chúc mừng Tết Âm lịch không?", "A. Có; B. Không", "A. Có", "trac_nghiem"),
        ('Kiến thức xã hội', "Chương trình nào được xem nhiều nhất đêm Giao thừa?", "A. Thời sự; B. Táo Quân; C. Ca nhạc; D. Phim hài", "B. Táo Quân", "trac_nghiem"),
        # Tự luận
        ('Kiến thức xã hội', "Vịnh nào của VN là di sản thế giới và điểm du lịch Tết nổi tiếng?", "", "Vịnh Hạ Long", "tu_luan"),
        ('Kiến thức xã hội', "Con giáp đứng đầu trong 12 con giáp là gì?", "", "Tý", "tu_luan"),
        ('Kiến thức xã hội', "Trận đại phá quân Thanh của Quang Trung diễn ra vào mùa nào?", "", "Mùa Xuân", "tu_luan"),
        ('Kiến thức xã hội', "Loại tiền in hình con vật của năm để làm quà gọi là gì?", "", "Tiền lì xì", "tu_luan"),
        ('Kiến thức xã hội', "Bài hát 'Khúc giao mùa' do cặp đôi nào thể hiện thành công nhất?", "", "Mỹ Linh & Minh Quân", "tu_luan"),

        # --- NEW BATCH: PHONG TỤC NGÀY TẾT ---
        ('Phong tục ngày Tết', "Lễ cúng ông Công ông Táo thường được tổ chức vào ngày nào âm lịch?", "A. 23 tháng Chạp; B. 15 tháng Chạp; C. 30 tháng Chạp; D. Mùng 1 Tết", "A. 23 tháng Chạp", "trac_nghiem"),
        ('Phong tục ngày Tết', "Người đầu tiên bước vào nhà sau thời khắc Giao thừa được gọi là gì?", "A. Người mở hàng; B. Người chúc Tết; C. Người xông đất; D. Người hái lộc", "C. Người xông đất", "trac_nghiem"),
        ('Phong tục ngày Tết', "Theo quan niệm dân gian, người ta thường mua gì đầu năm để cầu sự đậm đà, mặn mà?", "A. Mua đường; B. Mua muối; C. Mua gạo; D. Mua vàng", "B. Mua muối", "trac_nghiem"),
        ('Phong tục ngày Tết', "Tục lệ dựng cây Nêu trước sân nhà vào ngày Tết có ý nghĩa chính là gì?", "A. Để trang trí; B. Để xua đuổi ma quỷ; C. Để treo đèn lồng; D. Để chỉ đường cho tổ tiên", "B. Để xua đuổi ma quỷ", "trac_nghiem"),
        ('Phong tục ngày Tết', "Mâm cúng Giao thừa ngoài trời thường được gọi là lễ gì?", "A. Lễ Tất niên; B. Lễ Thượng nguyên; C. Lễ Tạ ơn; D. Lễ Trừ tịch", "D. Lễ Trừ tịch", "trac_nghiem"),
        ('Phong tục ngày Tết', "Tại sao người Việt thường có tục kiêng quét nhà vào mùng 1 Tết?", "A. Sợ quét mất tài lộc ra khỏi nhà; B. Sợ làm hỏng chổi; C. Để chổi được nghỉ ngơi; D. Sợ gây tiếng ồn", "A. Sợ quét mất tài lộc ra khỏi nhà", "trac_nghiem"),
        ('Phong tục ngày Tết', "Theo tục lệ, 'Mùng 1 Tết cha, mùng 2 Tết mẹ', vậy mùng 3 thường là Tết ai?", "A. Tết Bạn bè; B. Tết Anh em; C. Tết Thầy; D. Tết Ông bà", "C. Tết Thầy", "trac_nghiem"),
        ('Phong tục ngày Tết', "Hành động thăm viếng, chăm sóc mộ phần tổ tiên trước Tết gọi là gì?", "A. Thăm mộ; B. Tả mộ (Tạ mộ); C. Khai mộ; D. Viếng mộ", "B. Tả mộ (Tạ mộ)", "trac_nghiem"),
        ('Phong tục ngày Tết', "Phong tục 'Hái lộc' đầu năm thường được thực hiện vào thời điểm nào?", "A. Sáng mùng 1 Tết; B. Ngay sau thời khắc Giao thừa; C. Rằm tháng Giêng; D. Ngày hạ cây Nêu", "B. Ngay sau thời khắc Giao thừa", "trac_nghiem"),
        ('Phong tục ngày Tết', "Trong bao lì xì, màu sắc nào tượng trưng cho may mắn và niềm vui?", "A. Màu Vàng; B. Màu Đen; C. Màu Đỏ; D. Màu Trắng", "C. Màu Đỏ", "trac_nghiem"),

        # --- NEW BATCH: Ý NGHĨA CÁC MÓN ĂN ---
        ('Ý nghĩa các món ăn', "Bánh chưng hình vuông tượng trưng cho điều gì?", "A. Mặt trăng; B. Mặt trời; C. Mặt đất; D. Sự giàu sang", "C. Mặt đất", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "Món ăn nào ở miền Nam mang ý nghĩa mong cầu mọi khó khăn năm cũ qua đi?", "A. Thịt kho tàu; B. Canh khổ qua; C. Lạp xưởng; D. Dưa giá", "B. Canh khổ qua", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "Màu đỏ của xôi gấc tượng trưng cho điều gì?", "A. Sự ấm no; B. Sự trung thủy; C. Sự may mắn, tài lộc; D. Sự thanh khiết", "C. Sự may mắn, tài lộc", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "Trong mâm ngũ quả miền Nam, quả nào tượng trưng cho từ 'Vừa' trong 'Cầu vừa đủ xài'?", "A. Quả Sung; B. Quả Dừa; C. Quả Đu đủ; D. Quả Xoài", "B. Quả Dừa", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "Món thịt đông miền Bắc thường được ăn kèm với gì để trung hòa độ béo?", "A. Kim chi; B. Dưa cải; C. Dưa hành; D. Cà muối", "C. Dưa hành", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "Hạt dưa nhuộm đỏ trong khay mứt Tết mang ý nghĩa gì?", "A. Sự hanh thông, cát tường; B. Sự tiết kiệm; C. Sự sung túc; D. Sự bền bỉ", "A. Sự hanh thông, cát tường", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "Gạo nếp cái hoa vàng thường được dùng để làm gì trong dịp Tết?", "A. Nấu chè; B. Làm vỏ bánh chưng; C. Làm cốm; D. Nấu cháo", "B. Làm vỏ bánh chưng", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "'Con gà cục tác lá chanh'. Gà luộc cúng Tết thường được bày kèm với loại lá nào?", "A. Lá lốt; B. Lá húng; C. Lá tía tô; D. Lá chanh", "D. Lá chanh", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "Mứt Sen trần trong khay mứt Tết tượng trưng cho điều gì?", "A. Sự giàu có; B. Sự thanh tao, đài các; C. Sự ngọt ngào; D. Sự vất vả", "B. Sự thanh tao, đài các", "trac_nghiem"),
        ('Ý nghĩa các món ăn', "Ý nghĩa của nải chuối xanh trong mâm ngũ quả miền Bắc là gì?", "A. Để chuối lâu hỏng; B. Tượng trưng bàn tay ngửa che chở, đùm bọc; C. Tượng trưng cho tiền bạc; D. Chỉ để trang trí", "B. Tượng trưng bàn tay ngửa che chở, đùm bọc", "trac_nghiem"),

        # --- NEW BATCH: LOÀI HOA ---
        ('Loài hoa', "Loài hoa biểu tượng mùa xuân của miền Bắc là?", "A. Hoa Mai; B. Hoa Lan; C. Hoa Đào; D. Hoa Huệ", "C. Hoa Đào", "trac_nghiem"),
        ('Loài hoa', "Hoa Mai vàng miền Nam có bao nhiêu cánh thì được coi là cực kỳ may mắn?", "A. 4 cánh; B. 5 cánh; C. 8 cánh (Phát tài); D. 10 cánh", "C. 8 cánh (Phát tài)", "trac_nghiem"),
        ('Loài hoa', "Cây Quất 'Tứ quý' ngày Tết cần đảm bảo có các yếu tố nào?", "A. Rễ, thân, lá, cành; B. Quả chín, quả xanh, hoa và lộc lá; C. Đất, nước, chậu, phân bón; D. Chim, bướm, quả, hoa", "B. Quả chín, quả xanh, hoa và lộc lá", "trac_nghiem"),
        ('Loài hoa', "Loài đào có màu đỏ thẫm, cánh dày và kép được gọi là?", "A. Đào phai; B. Đào bạch; C. Đào bích; D. Đào rừng", "C. Đào bích", "trac_nghiem"),
        ('Loài hoa', "Hoa Cúc Vạn Thọ bày Tết mang mong muốn gì?", "A. Sự thông minh; B. Sống lâu, trường thọ; C. Sự giàu sang; D. Tình yêu", "B. Sống lâu, trường thọ", "trac_nghiem"),
        ('Loài hoa', "Loài hoa 'nàng tiên dưới nước' có hương thơm thanh khiết bày Tết là?", "A. Hoa Súng; B. Hoa Sen; C. Hoa Thủy Tiên; D. Hoa Bèo", "C. Hoa Thủy Tiên", "trac_nghiem"),
        ('Loài hoa', "Hoa Trạng Nguyên màu đỏ rực mang ý nghĩa gì cho con cháu?", "A. Sức khỏe; B. Thi cử đỗ đạt, thành công; C. Xinh đẹp; D. Giàu có", "B. Thi cử đỗ đạt, thành công", "trac_nghiem"),
        ('Loài hoa', "Mai tứ quý có đặc điểm nổi bật nào?", "A. Chỉ nở đúng mùng 1; B. Hoa màu trắng; C. Nở hoa quanh năm; D. Không có lá", "C. Nở hoa quanh năm", "trac_nghiem"),
        ('Loài hoa', "Theo truyền thuyết, hoa đào giúp con người bảo vệ nhà cửa bằng cách nào?", "A. Chống trộm; B. Xua đuổi tà ma; C. Đuổi côn trùng; D. Làm mát không khí", "B. Xua đuổi tà ma", "trac_nghiem"),
        ('Loài hoa', "Loài hoa có hình dáng giống mào của con gà trống thường bày Tết là?", "A. Hoa Thiên Nga; B. Hoa Lan; C. Hoa Mào Gà; D. Hoa Phượng", "C. Hoa Mào Gà", "trac_nghiem"),

        # --- NEW BATCH: NGÀY TẾT TRONG VĂN HỌC ---
        ('Ngày tết trong văn học', "Bài thơ 'Ông Đồ' gắn liền với hình ảnh loài hoa nào?", "A. Hoa Mai; B. Hoa Đào; C. Hoa Cúc; D. Hoa Lan", "B. Hoa Đào", "trac_nghiem"),
        ('Ngày tết trong văn học', "Ai là nhân vật làm ra bánh chưng, bánh giầy để dâng lên vua Hùng?", "A. Sơn Tinh; B. Thạch Sanh; C. Lang Liêu; D. Thánh Gióng", "C. Lang Liêu", "trac_nghiem"),
        ('Ngày tết trong văn học', "Hoàn thành vế đối: 'Thịt mỡ, dưa hành, câu đối đỏ / Cây nêu, ..., bánh chưng xanh'?", "A. Tràng pháo; B. Lì xì; C. Mứt Tết; D. Hoa đào", "A. Tràng pháo", "trac_nghiem"),
        ('Ngày tết trong văn học', "Nhân vật Xuân Tóc Đỏ trong tiểu thuyết 'Số Đỏ' phản ánh phong trào gì thời Pháp thuộc?", "A. Cần Vương; B. Duy Tân; C. Âu hóa lố lăng; D. Thơ mới", "C. Âu hóa lố lăng", "trac_nghiem"),
        ('Ngày tết trong văn học', "Tác giả của bài thơ 'Chợ Tết' tả cảnh làng quê rực rỡ sắc màu là?", "A. Xuân Diệu; B. Huy Cận; C. Đoàn Văn Cừ; D. Tế Hanh", "C. Đoàn Văn Cừ", "trac_nghiem"),
        ('Ngày tết trong văn học', "'Mùa xuân là Tết trồng cây...' là câu nói nổi tiếng của ai?", "A. Võ Nguyên Giáp; B. Hồ Chí Minh; C. Tố Hữu; D. Trần Phú", "B. Hồ Chí Minh", "trac_nghiem"),
        ('Ngày tết trong văn học', "Trong văn học, hình ảnh 'Nồi bánh chưng' đêm Giao thừa biểu tượng cho điều gì?", "A. Sự nghèo khó; B. Sự ấm no, sum vầy; C. Sự vất vả; D. Sự lãng phí", "B. Sự ấm no, sum vầy", "trac_nghiem"),
        ('Ngày tết trong văn học', "'Nhà thơ của đồng quê' nổi tiếng với bài 'Tết của mẹ tôi' là?", "A. Nguyễn Bính; B. Hàn Mặc Tử; C. Quang Dũng; D. Xuân Quỳnh", "A. Nguyễn Bính", "trac_nghiem"),
        ('Ngày tết trong văn học', "Câu nói 'Tháng Giêng là tháng ăn chơi' phản ánh điều gì?", "A. Sự lười biếng; B. Mùa lễ hội và nghỉ ngơi sau vụ mùa; C. Sự lãng phí; D. Việc bỏ bê công việc", "B. Mùa lễ hội và nghỉ ngơi sau vụ mùa", "trac_nghiem"),
        ('Ngày tết trong văn học', "Tập thơ 'Thơ thơ' mang hơi thở mùa xuân tình yêu là của ai?", "A. Chế Lan Viên; B. Xuân Diệu; C. Huy Cận; D. Lưu Trọng Lư", "B. Xuân Diệu", "trac_nghiem"),
        
        # --- NEW BATCH: CA DAO ---
        ('Ca dao', "'Mùng một Tết cha, mùng hai Tết mẹ, mùng ba...'?", "A. Tết bạn; B. Tết hàng xóm; C. Tết thầy; D. Tết ông bà", "C. Tết thầy", "trac_nghiem"),
        ('Ca dao', "'Đầu năm mua muối, cuối năm mua...'?", "A. Đường; B. Gạo; C. Vàng; D. Vôi", "D. Vôi", "trac_nghiem"),
        ('Ca dao', "Câu 'Ba mươi chưa phải là Tết' khuyên chúng ta điều gì?", "A. Nên đi chơi nhiều hơn; B. Đừng vội kết luận khi sự việc chưa kết thúc; C. Tết đến rất chậm; D. Phải dọn nhà nhanh", "B. Đừng vội kết luận khi sự việc chưa kết thúc", "trac_nghiem"),
        ('Ca dao', "'Số cô chẳng giàu thì nghèo, Ngày ba mươi Tết có thịt treo trong nhà'. Câu này thuộc thể loại?", "A. Ca dao than thân; B. Ca dao châm biếm bói toán; C. Ca dao lao động; D. Kinh nghiệm sản xuất", "B. Ca dao châm biếm bói toán", "trac_nghiem"),
        ('Ca dao', "'Tháng Giêng là tháng ăn chơi, Tháng Hai trồng đậu, trồng khoai, trồng...'?", "A. Ngô; B. Lúa; C. Cà; D. Bầu", "C. Cà", "trac_nghiem"),
        ('Ca dao', "'Cu kêu ba tiếng cu kêu, Cho mau tới Tết dựng ... ăn chè'?", "A. Cây cột; B. Cây nêu; C. Cây sào; D. Cái rạp", "B. Cây nêu", "trac_nghiem"),
        ('Ca dao', "'Có rau có cháo cũng xong, Miễn là có cái ... trong ngày xuân'?", "A. Giò chả; B. Bánh chưng; C. Bao lì xì; D. Tràng pháo", "B. Bánh chưng", "trac_nghiem"),
        ('Ca dao', "'Dù ai đi ngược về xuôi, Nhớ ngày Giỗ Tổ mùng mười tháng ba'. Lễ hội này diễn ra vào mùa nào?", "A. Mùa Xuân; B. Mùa Hạ; C. Mùa Thu; D. Mùa Đông", "A. Mùa Xuân", "trac_nghiem"),
        ('Ca dao', "Câu 'Ăn bánh chưng nhớ tổ tiên' nhắc nhở đạo lý gì?", "A. Tiết kiệm; B. Cần cù; C. Uống nước nhớ nguồn; D. Nhân nghĩa", "C. Uống nước nhớ nguồn", "trac_nghiem"),
        ('Ca dao', "Hình ảnh 'Hoa đào' trong ca dao thường gắn với tín hiệu gì?", "A. Mùa lúa chín; B. Tết đến xuân về; C. Mùa tựu trường; D. Cảnh chia ly", "B. Tết đến xuân về", "trac_nghiem"),
        
        # --- NEW BATCH: KIẾN THỨC XÃ HỘI ---
        ('Kiến thức xã hội', "Năm 2026 theo âm lịch Việt Nam là năm con gì?", "A. Năm Tỵ (Con Rắn); B. Năm Ngọ (Con Ngựa); C. Năm Mùi (Con Dê); D. Năm Thân (Con Khỉ)", "B. Năm Ngọ (Con Ngựa)", "trac_nghiem"),
        ('Kiến thức xã hội', "Quốc gia nào ở Đông Á đã chuyển hẳn sang ăn Tết theo Dương lịch?", "A. Trung Quốc; B. Hàn Quốc; C. Nhật Bản; D. Việt Nam", "C. Nhật Bản", "trac_nghiem"),
        ('Kiến thức xã hội', "Chương trình 'Gặp nhau cuối năm' (Táo Quân) thường phát sóng lúc nào?", "A. Sáng mùng 1; B. Tối 23 tháng Chạp; C. Đêm Giao thừa (30 Tết); D. Mùng 3 Tết", "C. Đêm Giao thừa (30 Tết)", "trac_nghiem"),
        ('Kiến thức xã hội', "Thành phố nào nổi tiếng với nhiều điểm bắn pháo hoa Giao thừa nhất Việt Nam?", "A. Hải Phòng; B. Đà Nẵng; C. Hà Nội; D. Cần Thơ", "C. Hà Nội", "trac_nghiem"),
        ('Kiến thức xã hội', "Việt Nam có con 'Mèo' trong 12 con giáp, còn Trung Quốc thay bằng con gì?", "A. Con Cừu; B. Con Thỏ; C. Con Báo; D. Con Voi", "B. Con Thỏ", "trac_nghiem"),
        ('Kiến thức xã hội', "Rằm tháng Giêng còn được gọi là Tết gì?", "A. Tết Đoan Ngọ; B. Tết Trung Thu; C. Tết Nguyên Tiêu; D. Tết Trùng Cửu", "C. Tết Nguyên Tiêu", "trac_nghiem"),
        ('Kiến thức xã hội', "Chiến thắng Ngọc Hồi - Đống Đa của vua Quang Trung diễn ra vào dịp nào?", "A. Tết Nguyên Đán; B. Tết Trung Thu; C. Tết Đoan Ngọ; D. Tết Hàn Thực", "A. Tết Nguyên Đán", "trac_nghiem"),
        ('Kiến thức xã hội', "Tục 'Khai bút đầu xuân' của học sinh, sinh viên mang ý nghĩa gì?", "A. Để hết mực; B. Để làm bài tập về nhà; C. Cầu mong học hành, thi cử thuận lợi; D. Để khoe bút mới", "C. Cầu mong học hành, thi cử thuận lợi", "trac_nghiem"),
        ('Kiến thức xã hội', "Tết Nguyên Đán thường rơi vào khoảng thời gian nào của Dương lịch?", "A. Tháng 12 sang tháng 1; B. Cuối tháng 1 sang tháng 2; C. Cuối tháng 2 sang tháng 3; D. Cố định ngày 1/1", "B. Cuối tháng 1 sang tháng 2", "trac_nghiem"),
        ('Kiến thức xã hội', "Bài hát 'Happy New Year' kinh điển đêm Giao thừa là của nhóm nhạc nào?", "A. Modern Talking; B. Boney M; C. ABBA; D. Westlife", "C. ABBA", "trac_nghiem")
    ]

    sql = "INSERT INTO questions (category, content, options, answer, type) VALUES (%s, %s, %s, %s, %s)"
    cursor.executemany(sql, questions)
    conn.commit()
    print(f"Inserted {cursor.rowcount} questions.")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    init_db()
