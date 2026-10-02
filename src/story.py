# -*- coding: utf-8 -*-
"""Kịch bản "Năm Anh Em Nhà Mình" – bản Trung thu, 7 nhân vật, lồng tiếng từng người.

Mỗi cảnh gồm: id, nền (bg), danh sách câu. Mỗi câu là (ai_nói, lời, [khoá]).
ai_nói: nar (người dẫn chuyện) | ma (má, ngoài khung hình) | kaka | puka | moon | sam | muoi | eric | lu | all.
Khoá (tuỳ chọn) để phần biên đạo (scenes.py) bám theo mốc thời gian của câu đó.
"""

TITLE = "Nhà Mình Vui Trung Thu"

NAMES = {"nar": "", "ma": "Má", "kaka": "Kaka", "puka": "Puka", "moon": "Moon", "sam": "Sam", "muoi": "Muội", "eric": "Eric", "lu": "Lu", "all": "Cả nhà"}


def _l(who, text, key=None):
    return dict(who=who, text=text, key=key)


SCENES = [
    dict(id="01_intro", bg="exterior", lines=[
        _l("nar", "Ở một con hẻm nhỏ, có một ngôi nhà lúc nào cũng ồn ào như cái chợ."),
        _l("nar", "Trong nhà có sáu anh em, một bé cún, và một ngàn trò quậy.", "kids"),
        _l("all", "Chào mấy bé!", "hello"),
        _l("nar", "Sắp tới Trung thu rồi, mình vô nhà coi thử tụi nhỏ chuẩn bị gì nha!", "zoom"),
    ]),
    dict(id="02_kaka", bg="hall", lines=[
        _l("kaka", "Chào mấy bé! Anh là Kaka, anh Hai của cái nhà này.", "intro"),
        _l("nar", "Kaka nghịch ngợm, siêu lì, và mê nhất là múa lân."),
        _l("kaka", "Trung thu này anh cầm đầu lân! Coi anh tập nè! Tùng tùng cắc!", "dance"),
        _l("nar", "Bịch! Đụng trúng kệ giày.", "drop"),
        _l("kaka", "Hì hì, không sao! Lì mà!", "li"),
    ]),
    dict(id="03_puka", bg="hall", lines=[
        _l("puka", "Puka nè! Puka là chị Ba, siêu quậy số một!", "intro"),
        _l("nar", "Puka mà quậy thì cả nhà chạy không kịp."),
        _l("puka", "Hù!", "boo"),
        _l("kaka", "Oái! Puka!", "oai"),
        _l("puka", "Hi hi! Dính rồi!", "hihi"),
    ]),
    dict(id="04_moon", bg="hall", lines=[
        _l("moon", "Mình là Moon. Mình lớn tuổi nhất nhà, mà vẫn phải kêu anh Hai, chị Ba. Kỳ ghê!", "intro"),
        _l("nar", "Moon ham học, lúc nào cũng ôm cuốn sách, và là người lo cho cả đám."),
        _l("moon", "Trung thu phải có lồng đèn. Để Moon làm!", "lantern"),
    ]),
    dict(id="05_sam", bg="hall", lines=[
        _l("sam", "Sam nè! Sam điệu nhất nhà!", "intro"),
        _l("sam", "Đồ ngủ mặt cười, đẹp hông?", "twirl"),
        _l("nar", "Sam điệu đà, nhí nhảnh, mà lì thì không thua anh Hai."),
        _l("ma", "Sam ơi, phụ má!", "call"),
        _l("sam", "Chút nữa má ơi! Sam đang đẹp!", "later"),
    ]),
    dict(id="06_muoi", bg="living", lines=[
        _l("muoi", "Muội nè! Muội thích ăn nhất nhà!", "intro"),
        _l("nar", "Muội thích ăn, thích giành đồ chơi, và khoái nhất là chọc em Eric."),
        _l("muoi", "Bánh trung thu đâu? Muội ăn thử một miếng thôi!", "cake"),
        _l("moon", "Muội! Bánh để tối cúng trăng mà!", "stop"),
        _l("muoi", "Ưm... ngon quá!", "yum"),
    ]),
    dict(id="07_eric", bg="living", lines=[
        _l("eric", "Eric nè! Eric là em Út!", "intro"),
        _l("nar", "Eric siêu quậy, mà cũng siêu mít ướt."),
        _l("muoi", "Eric, lồng đèn này của chị!", "grab"),
        _l("eric", "Oa oa oa! Chị Muội giành của em!", "cry"),
        _l("kaka", "Muội! Trả em đi!", "kaka"),
        _l("eric", "Hi hi, hết khóc rồi!", "ok"),
    ]),
    dict(id="08_lu", bg="living", lines=[
        _l("lu", "Gâu! Gâu gâu!", "bark"),
        _l("nar", "Còn đây là Lu, chú cún lông xoăn, biếng ăn mà ham chơi."),
        _l("moon", "Lu, ăn cơm đi!", "food"),
        _l("lu", "Gâu...", "nope"),
        _l("nar", "Lu lắc đầu, rồi thấy anh chị đi đâu là lạch bạch đòi theo đó.", "run"),
    ]),
    dict(id="09_plan", bg="living", lines=[
        _l("kaka", "Tối nay cả nhà múa lân! Anh cầm đầu lân!", "plan"),
        _l("sam", "Sam với Puka làm đuôi lân!", "tail"),
        _l("moon", "Moon đánh trống. Muội cầm lồng đèn.", "drum"),
        _l("muoi", "Muội muốn cầm bánh!", "cakeagain"),
        _l("kaka", "Eric làm Ông Địa nha!", "ongdia"),
        _l("eric", "Ông Địa là gì?", "what"),
        _l("kaka", "Là ông bụng bự, cầm quạt, cười hoài!", "explain"),
        _l("eric", "Dạ chịu!", "yes"),
    ]),
    dict(id="10_practice", bg="hall", lines=[
        _l("nar", "Cả nhà bắt đầu tập. Và... loạn như cái chợ.", "start"),
        _l("moon", "Tùng tùng cắc! Tùng tùng cắc!", "drum"),
        _l("kaka", "Lân nhảy nè!", "jump"),
        _l("nar", "Đầu lân nhảy một đường, đuôi lân chạy một nẻo.", "split"),
        _l("puka", "Anh Hai chạy chậm thôi!", "slow"),
        _l("sam", "Tóc Sam rối hết rồi!", "hair"),
        _l("nar", "Lu phóng tới cắn đuôi lân. Bịch! Cả đám té chồng lên nhau.", "fall"),
        _l("eric", "Oa oa! Đau quá!", "cry"),
        _l("moon", "Nín nha Út. Mình tập lại từ đầu!", "again"),
    ]),
    dict(id="11_fight", bg="living", lines=[
        _l("nar", "Chiều tới, Muội lại giở trò.", "start"),
        _l("muoi", "Quạt Ông Địa của Eric đẹp quá! Cho chị mượn!", "grab"),
        _l("eric", "Hông! Của em!", "no"),
        _l("muoi", "Chị lớn hơn, chị cầm!", "pull"),
        _l("eric", "Oa oa oa!", "cry"),
        _l("nar", "Bất thình lình, Lu phóng tới ngoạm cái quạt chạy mất tiêu!", "lu"),
        _l("all", "Ơ! Lu!", "o"),
        _l("nar", "Cả nhà rượt theo Lu quanh bộ ghế xanh. Kaka trượt chân, té cái bịch!", "chase"),
        _l("puka", "Ha ha! Anh Hai té nữa rồi!", "laugh"),
        _l("nar", "Lu dừng lại, thả cái quạt xuống trước mặt Eric.", "stop"),
        _l("muoi", "Thôi... quạt của Út. Chị xin lỗi.", "sorry"),
        _l("eric", "Hết khóc! Chị Muội cầm chung với em nha!", "share"),
    ]),
    dict(id="12_midautumn", bg="yard", lines=[
        _l("nar", "Đêm Trung thu. Trăng tròn vành vạnh, lồng đèn giăng đầy sân.", "night"),
        _l("moon", "Tùng! Tùng! Cắc! Tùng! Tùng! Cắc!", "drum"),
        _l("kaka", "Lân tới rồi đây!", "lion"),
        _l("nar", "Kaka cầm đầu lân nhảy cao, lắc đầu, chớp mắt. Sam với Puka vẫy đuôi theo nhịp trống.", "dance"),
        _l("eric", "Ông Địa đây! Ha ha ha!", "ongdia"),
        _l("nar", "Eric bụng bự phe phẩy cái quạt, lạch bạch chạy quanh con lân. Muội cầm lồng đèn múa theo, tay kia cầm bánh.", "fan"),
        _l("muoi", "Múa hay quá! Muội thưởng cho lân miếng bánh nè!", "reward"),
        _l("lu", "Gâu gâu gâu!", "lu"),
        _l("nar", "Lu chạy vòng vòng sủa theo nhịp, cả xóm vỗ tay rần rần.", "clap"),
        _l("all", "Hoan hô! Hoan hô!", "cheer"),
    ]),
    dict(id="13_ending", bg="yard", lines=[
        _l("nar", "Múa xong, cả nhà ngồi dưới trăng, chia nhau cái bánh trung thu.", "sit"),
        _l("muoi", "Miếng to nhất cho Út nè!", "give"),
        _l("eric", "Chị Muội tốt ghê!", "thanks"),
        _l("nar", "Có lúc giận, có lúc giành, nhưng anh em trong nhà lúc nào cũng thương nhau.", "love"),
        _l("nar", "Như ông bà mình hay nói: anh em như thể tay chân, đó các bé!", "moral"),
        _l("all", "Anh em thương nhau!", "cheer"),
        _l("lu", "Gâu!", "lu"),
    ]),
    dict(id="14_outro", bg="exterior_night", lines=[
        _l("nar", "Hết rồi!", "end"),
        _l("all", "Chúc mấy bé Trung thu vui! Hẹn gặp lại nha!", "bye"),
    ]),
]


def all_lines():
    for s in SCENES:
        for i, line in enumerate(s["lines"]):
            yield s["id"], i, line
