# -*- coding: utf-8 -*-
"""Kịch bản "Năm Anh Em Nhà Mình" (bản lồng tiếng từng nhân vật).

Mỗi cảnh gồm: id, nền (bg), danh sách câu. Mỗi câu là (ai_nói, lời, [khoá]).
ai_nói: nar (người dẫn chuyện) | ma (má, ngoài khung hình) | kaka | puka | moon | sam | lu | all (cả nhà).
Khoá (tuỳ chọn) để phần biên đạo (scenes.py) bám theo mốc thời gian của câu đó.
"""

TITLE = "Năm Anh Em Nhà Mình"

NAMES = {"nar": "", "ma": "Má", "kaka": "Kaka", "puka": "Puka", "moon": "Moon", "sam": "Sam", "lu": "Lu", "all": "Cả nhà"}


def _l(who, text, key=None):
    return dict(who=who, text=text, key=key)


SCENES = [
    dict(id="01_intro", bg="exterior", lines=[
        _l("nar", "Ở một con hẻm nhỏ, có một ngôi nhà lúc nào cũng ồn ào như cái chợ."),
        _l("nar", "Trong nhà có bốn anh em, một bé cún, và một ngàn trò quậy.", "kids"),
        _l("all", "Chào mấy bé!", "hello"),
        _l("nar", "Mình vô nhà coi thử tụi nhỏ đang quậy gì nha!", "zoom"),
    ]),
    dict(id="02_kaka", bg="hall", lines=[
        _l("kaka", "Chào mấy bé! Anh là Kaka, anh Hai của cái nhà này.", "intro"),
        _l("nar", "Kaka ham chơi dữ lắm, lại hài hước, nhà có gì cũng lấy ra chơi được."),
        _l("kaka", "Coi anh tung dép nè! Một, hai, ba!", "juggle"),
        _l("nar", "Bịch! Dép rớt trúng đầu.", "drop"),
        _l("kaka", "Hì hì, không sao! Lì mà!", "li"),
        _l("nar", "Anh Hai lì vậy đó, nhưng thương mấy đứa em hết sức, đi đâu cũng dắt theo.", "love"),
    ]),
    dict(id="03_puka", bg="hall", lines=[
        _l("puka", "Puka nè! Puka là chị Ba!", "intro"),
        _l("nar", "Puka bướng bỉnh, nghịch ngợm số một."),
        _l("puka", "Số một luôn!", "one"),
        _l("nar", "Sáng nào má kêu đi học, Puka cũng chun xuống gầm giường, trùm mền kín mít.", "blanket"),
        _l("ma", "Puka ơi, đi học!", "call"),
        _l("puka", "Hông! Hông! Hông đi đâu!", "no"),
    ]),
    dict(id="04_moon", bg="hall", lines=[
        _l("moon", "Mình là Moon. Mình lớn tuổi nhất nhà...", "intro"),
        _l("nar", "Nhưng tính theo vai vế thì Moon lại là em của anh Hai với chị Ba đó nha!", "weird"),
        _l("kaka", "Kêu anh Hai đi, Moon!", "call"),
        _l("moon", "Dạ... anh Hai. Kỳ ghê!", "sigh"),
        _l("nar", "Moon ham học, lúc nào cũng ôm cuốn sách, và thích nhất là chăm mấy đứa nhỏ.", "book"),
        _l("sam", "Chị Moon ơi, ôm!", "hug"),
    ]),
    dict(id="05_sam", bg="hall", lines=[
        _l("sam", "Sam nè! Sam là em Út, nhỏ nhất nhà!", "intro"),
        _l("sam", "Hôm nay Sam mặc đồ bông hồng, đẹp hông?", "twirl"),
        _l("nar", "Sam điệu đà, nghịch ngợm, lười học, nhưng làm mặt hề là số dzách!"),
        _l("sam", "Bleeee!", "face"),
        _l("all", "Ha ha ha!", "laugh"),
    ]),
    dict(id="06_lu", bg="living", lines=[
        _l("lu", "Gâu! Gâu gâu!", "bark"),
        _l("nar", "Còn đây là Lu, chú cún lông xoăn màu nâu, biếng ăn mà ham chơi."),
        _l("moon", "Lu, ăn cơm đi!", "food"),
        _l("lu", "Gâu...", "nope"),
        _l("nar", "Lu lắc đầu, rồi thấy anh chị chạy đâu là lạch bạch chạy theo đó.", "run"),
    ]),
    dict(id="07_morning", bg="bedroom", lines=[
        _l("ma", "Mấy đứa ơi, dậy đi học!", "call"),
        _l("kaka", "Năm phút nữa má ơi...", "kaka"),
        _l("puka", "Puka đang ngủ, xin đừng làm phiền!", "puka"),
        _l("sam", "Sam biến mất rồi!", "sam"),
        _l("moon", "Để Moon lo!", "moon"),
        _l("lu", "Gâu gâu gâu!", "lu"),
    ]),
    dict(id="08_moon_finds", bg="bedroom", lines=[
        _l("moon", "Puka ơi, ra đi! Hôm nay cô cho vẽ tranh nè!", "moon1"),
        _l("puka", "Thiệt hông?", "puka1"),
        _l("moon", "Thiệt mà!", "moon2"),
        _l("puka", "Vậy đi liền!", "puka2"),
        _l("moon", "Sam ơi, đi học về chị kể chuyện con khủng long ăn chay.", "moon3"),
        _l("sam", "Ủa, khủng long mà ăn chay hả? Kể liền đi!", "sam1"),
    ]),
    dict(id="09_kaka_monkey", bg="hall", lines=[
        _l("kaka", "Nhìn anh nè! Ú ù ú! Anh là khỉ Kaka!", "monkey"),
        _l("nar", "Anh Hai giả khỉ, đi lạch bạch, nhăn mặt méo mó."),
        _l("sam", "Anh Hai giống khỉ thiệt luôn!", "sam"),
        _l("kaka", "Ê! Nói gì đó!", "e"),
        _l("nar", "Puka cười té ghế, Sam cười lăn ra sàn. Cười xong là quên cả lười, cả đám xách cặp chạy đi học.", "go"),
        _l("lu", "Gâu gâu!", "lu"),
        _l("kaka", "Lu ở nhà coi nhà nha!", "stay"),
    ]),
    dict(id="10_fight", bg="living", lines=[
        _l("nar", "Chiều về, Puka và Sam giành nhau một con gấu bông.", "start"),
        _l("puka", "Gấu của chị!", "p1"),
        _l("sam", "Của em! Em thấy trước!", "s1"),
        _l("puka", "Chị lớn hơn!", "p2"),
        _l("sam", "Em nhỏ hơn!", "s2"),
        _l("nar", "Bất thình lình, Lu phóng tới ngoạm con gấu chạy mất tiêu!", "lu"),
        _l("all", "Ơ! Lu!", "o"),
    ]),
    dict(id="11_chase", bg="living", lines=[
        _l("kaka", "Để anh bắt cho!", "kaka"),
        _l("nar", "Cả nhà rượt theo Lu, chạy vòng quanh bộ ghế xanh.", "chase"),
        _l("kaka", "Oái!", "slip"),
        _l("nar", "Kaka trượt chân té cái bịch!", "fall"),
        _l("puka", "Ha ha! Anh Hai té!", "puka"),
        _l("kaka", "Hông có đau... nha.", "ok"),
        _l("nar", "Lu dừng lại, thả con gấu xuống, le lưỡi như muốn nói: chơi chung vui hơn mà!", "stop"),
    ]),
    dict(id="12_lesson", bg="living", lines=[
        _l("puka", "Thôi... em chơi trước đi. Chị chơi sau.", "give"),
        _l("sam", "Thiệt hông? Chị Ba tốt ghê!", "hug"),
        _l("moon", "Giờ cả nhà học bài chung nha!", "study"),
        _l("puka", "Dạ...", "da1"),
        _l("sam", "Dạ...", "da2"),
        _l("kaka", "Học xong anh kể chuyện cười!", "promise"),
        _l("puka", "Học liền!", "now"),
        _l("kaka", "Đố nè: con gì càng to càng nhẹ?", "riddle"),
        _l("sam", "Con gì?", "what"),
        _l("kaka", "Con... bong bóng!", "answer"),
        _l("all", "Ha ha ha ha!", "laugh"),
    ]),
    dict(id="13_ending", bg="living", lines=[
        _l("nar", "Tối đó, năm anh em nằm chen chúc trên ghế xanh, Lu nằm ở giữa."),
        _l("nar", "Có lúc giận, có lúc giành, nhưng anh em trong nhà lúc nào cũng thương nhau.", "love"),
        _l("nar", "Như ông bà mình hay nói: anh em như thể tay chân, đó các bé!", "moral"),
        _l("all", "Anh em thương nhau!", "cheer"),
        _l("lu", "Gâu!", "lu"),
    ]),
    dict(id="14_outro", bg="exterior_night", lines=[
        _l("nar", "Hết rồi!", "end"),
        _l("all", "Hẹn gặp lại mấy bé nha!", "bye"),
    ]),
]


def all_lines():
    for s in SCENES:
        for i, line in enumerate(s["lines"]):
            yield s["id"], i, line
