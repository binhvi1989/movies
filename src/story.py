# -*- coding: utf-8 -*-
"""Kịch bản thuyết minh: "Năm Anh Em Nhà Mình".

Mỗi cảnh (scene) gồm: id, tên nền (bg), danh sách câu thuyết minh.
Thời lượng mỗi cảnh được tính tự động theo độ dài file âm thanh thuyết minh.
"""

TITLE = "Năm Anh Em Nhà Mình"

SCENES = [
    dict(
        id="01_intro",
        bg="exterior",
        lines=[
            "Ở một con hẻm nhỏ, có một ngôi nhà lúc nào cũng rộn ràng tiếng cười.",
            "Trong nhà có bốn anh em, và một bé cún tên Lu.",
            "Hôm nay mình cùng vô nhà coi thử tụi nhỏ đang làm gì nha!",
        ],
    ),
    dict(
        id="02_kaka",
        bg="hall",
        lines=[
            "Đây là anh Hai Kaka, lớn nhất nhà.",
            "Kaka ham chơi dữ lắm, lại hài hước, kể chuyện tiếu lâm là cả nhà cười lăn.",
            "Mà anh Hai lì lắm nha, bị ba má rầy mà vẫn cười tỉnh bơ.",
            "Nhưng anh thương mấy đứa em hết sức, đi đâu cũng dắt theo.",
        ],
    ),
    dict(
        id="03_puka",
        bg="hall",
        lines=[
            "Còn đây là chị Ba Puka.",
            "Puka bướng bỉnh, nghịch ngợm số một.",
            "Sáng nào má kêu đi học, Puka cũng chun xuống gầm giường, trùm mền kín mít.",
            "Con hông đi đâu!",
        ],
    ),
    dict(
        id="04_moon",
        bg="hall",
        lines=[
            "Kế tiếp là Moon.",
            "Chuyện lạ là Moon lớn tuổi nhất nhà, nhưng tính theo vai vế thì lại là em của anh Hai với chị Ba đó nha!",
            "Moon ham học, lúc nào cũng ôm cuốn sách, và thích nhất là chăm mấy đứa nhỏ.",
        ],
    ),
    dict(
        id="05_sam",
        bg="hall",
        lines=[
            "Và đây là em Út Sam, nhỏ nhất nhà.",
            "Sam điệu đà lắm, có bộ đồ bông nào là mặc liền.",
            "Sam nghịch ngợm, lười học, mà mỗi lần làm mặt hề là ai cũng phải bật cười.",
        ],
    ),
    dict(
        id="06_lu",
        bg="living",
        lines=[
            "Cuối cùng là Lu, chú cún lông xoăn màu nâu.",
            "Lu biếng ăn mà ham chơi, thấy anh chị chạy đâu là lạch bạch chạy theo đó.",
        ],
    ),
    dict(
        id="07_morning",
        bg="bedroom",
        lines=[
            "Sáng thứ Hai. Má kêu: Mấy đứa ơi, dậy đi học!",
            "Kaka còn ngáp. Puka trốn dưới gầm giường. Sam núp sau cái tủ giày.",
            "Chỉ có Moon là đã thay đồ chỉnh tề.",
            "Còn Lu thì chạy vòng vòng sủa gâu gâu!",
        ],
    ),
    dict(
        id="08_moon_finds",
        bg="bedroom",
        lines=[
            "Moon đi tìm từng đứa.",
            "Puka ơi, ra đi, hôm nay cô cho vẽ tranh nè!",
            "Puka ló đầu ra: Thiệt hông? Thiệt mà!",
            "Moon lại dỗ Sam: Út đi học, chiều về chị kể chuyện cho nghe.",
        ],
    ),
    dict(
        id="09_kaka_monkey",
        bg="hall",
        lines=[
            "Anh Hai Kaka thấy vậy mới bày trò.",
            "Anh giả làm con khỉ đi lạch bạch, nhăn mặt méo mó.",
            "Puka cười té ghế, Sam cười lăn ra sàn.",
            "Cười xong là quên cả lười, cả đám hớn hở xách cặp đi học.",
        ],
    ),
    dict(
        id="10_fight",
        bg="living",
        lines=[
            "Chiều về, Puka và Sam giành nhau một con gấu bông.",
            "Của em! Của chị!",
            "Hai chị em kéo qua kéo lại.",
            "Bất thình lình, Lu phóng tới ngoạm con gấu chạy mất tiêu!",
        ],
    ),
    dict(
        id="11_chase",
        bg="living",
        lines=[
            "Cả nhà rượt theo Lu, chạy vòng quanh bộ ghế xanh.",
            "Kaka trượt chân té cái bịch, Moon đỡ Sam, Puka cười hết cỡ.",
            "Lu dừng lại, thả con gấu xuống, le lưỡi như muốn nói: Chơi chung vui hơn mà!",
        ],
    ),
    dict(
        id="12_lesson",
        bg="living",
        lines=[
            "Puka ngẫm nghĩ, rồi đưa con gấu cho Sam: Thôi em chơi trước đi, chị chơi sau.",
            "Sam ôm chị thiệt chặt.",
            "Moon mở sách ra: Giờ học bài chung nha!",
            "Lần đầu tiên Puka với Sam ngồi học ngoan ơi là ngoan, còn Kaka ngồi kế bên, kể chuyện cười.",
        ],
    ),
    dict(
        id="13_ending",
        bg="living",
        lines=[
            "Tối đó, năm anh em nằm chen chúc trên ghế xanh, Lu nằm ở giữa.",
            "Có lúc giận, có lúc giành, nhưng anh em trong nhà lúc nào cũng thương nhau.",
            "Như ông bà mình hay nói: Anh em như thể tay chân, đó các bé!",
        ],
    ),
    dict(
        id="14_outro",
        bg="exterior_night",
        lines=[
            "Hết rồi! Hẹn gặp lại mấy bé trong câu chuyện sau nha!",
        ],
    ),
]


def all_lines():
    for s in SCENES:
        for i, line in enumerate(s["lines"]):
            yield s["id"], i, line
