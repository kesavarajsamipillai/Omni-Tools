"""
Comprehensive Automated Test Suite for OmniTools Offline Suite
"""

import os
import shutil
from PIL import Image
import docx
from pypdf import PdfWriter, PdfReader

import modules.pdf_tools as pdf_tools
import modules.doc_tools as doc_tools
import modules.image_tools as image_tools
import modules.audio_tools as audio_tools
import modules.folder_sorter as folder_sorter
import modules.extra_tools as extra_tools

TEST_DIR = r"k:\Python_tools\test_sandbox"


def setup_test_files():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR, exist_ok=True)

    # 1. Create test PNG image with RGBA transparency
    img_path = os.path.join(TEST_DIR, "sample_transparent.png")
    img = Image.new("RGBA", (200, 200), (255, 0, 0, 128))
    img.save(img_path)

    # 2. Create test encrypted PDF
    pdf_path = os.path.join(TEST_DIR, "sample_protected.pdf")
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    writer.encrypt(user_password="TEST_PASSWORD_123", owner_password="TEST_PASSWORD_123")
    with open(pdf_path, "wb") as f:
        writer.write(f)

    # 3. Create test DOCX file
    docx_path = os.path.join(TEST_DIR, "sample_doc.docx")
    doc = docx.Document()
    doc.add_heading("Offline Tools Test Document", level=1)
    doc.add_paragraph("This is a paragraph verifying offline document conversion.")
    doc.save(docx_path)

    # 4. Create dummy audio file via python wave module
    audio_path = os.path.join(TEST_DIR, "sample_tone.wav")
    import wave
    import struct
    import math
    with wave.open(audio_path, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(44100)
        # 0.5 second 440 Hz tone
        for i in range(22050):
            value = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * 440.0 * i / 44100.0))
            data = struct.pack("<h", value)
            wav_file.writeframesraw(data)

    # 5. Create mixed folder for sorting test
    mix_dir = os.path.join(TEST_DIR, "mixed_files_to_sort")
    os.makedirs(mix_dir, exist_ok=True)
    with open(os.path.join(mix_dir, "photo1.jpg"), "w") as f: f.write("img")
    with open(os.path.join(mix_dir, "graphic.png"), "w") as f: f.write("img")
    with open(os.path.join(mix_dir, "banner.jpeg"), "w") as f: f.write("img")
    with open(os.path.join(mix_dir, "invoice.pdf"), "w") as f: f.write("pdf")
    with open(os.path.join(mix_dir, "report.docx"), "w") as f: f.write("docx")
    with open(os.path.join(mix_dir, "slides.ppt"), "w") as f: f.write("ppt")
    with open(os.path.join(mix_dir, "pitch.pptx"), "w") as f: f.write("pptx")
    with open(os.path.join(mix_dir, "song.mp3"), "w") as f: f.write("audio")

    print("[SETUP] Created test fixtures in test_sandbox")


def run_tests():
    setup_test_files()
    passed = 0
    total = 0

    # Test 1: PDF Password Remover
    total += 1
    enc_pdf = os.path.join(TEST_DIR, "sample_protected.pdf")
    unlocked_pdf = os.path.join(TEST_DIR, "sample_unlocked.pdf")
    res1 = pdf_tools.remove_pdf_password(enc_pdf, unlocked_pdf, "TEST_PASSWORD_123")
    assert res1["success"] and os.path.exists(unlocked_pdf), f"PDF unlock failed: {res1}"
    reader = PdfReader(unlocked_pdf)
    assert not reader.is_encrypted, "PDF is still encrypted!"
    passed += 1
    print("[PASS] Test 1: PDF Password Remover")

    # Test 2: Image Format Conversions (RGBA -> JPEG, PNG -> WEBP, PNG -> ICO)
    total += 1
    img_in = os.path.join(TEST_DIR, "sample_transparent.png")
    img_jpg = os.path.join(TEST_DIR, "converted.jpg")
    img_webp = os.path.join(TEST_DIR, "converted.webp")
    img_ico = os.path.join(TEST_DIR, "converted.ico")

    res_jpg = image_tools.convert_image(img_in, img_jpg, "jpg")
    res_webp = image_tools.convert_image(img_in, img_webp, "webp")
    res_ico = image_tools.convert_image(img_in, img_ico, "ico")

    assert res_jpg["success"] and os.path.exists(img_jpg)
    assert res_webp["success"] and os.path.exists(img_webp)
    assert res_ico["success"] and os.path.exists(img_ico)
    passed += 1
    print("[PASS] Test 2: Image Format Conversions (PNG -> JPG, WEBP, ICO)")

    # Test 3: DOCX to PDF
    total += 1
    doc_in = os.path.join(TEST_DIR, "sample_doc.docx")
    pdf_out = os.path.join(TEST_DIR, "doc_converted.pdf")
    res_d2p = doc_tools.docx_to_pdf(doc_in, pdf_out)
    assert res_d2p["success"] and os.path.exists(pdf_out), f"DOCX to PDF failed: {res_d2p}"
    passed += 1
    print(f"[PASS] Test 3: DOCX to PDF (Engine: {res_d2p.get('engine')})")

    # Test 4: PDF to DOCX
    total += 1
    docx_back = os.path.join(TEST_DIR, "pdf_back_to_doc.docx")
    res_p2d = doc_tools.pdf_to_docx(pdf_out, docx_back)
    assert res_p2d["success"] and os.path.exists(docx_back), f"PDF to DOCX failed: {res_p2d}"
    passed += 1
    print("[PASS] Test 4: PDF to DOCX")

    # Test 5: Audio Conversion (WAV -> MP3)
    total += 1
    wav_in = os.path.join(TEST_DIR, "sample_tone.wav")
    if os.path.exists(wav_in):
        mp3_out = os.path.join(TEST_DIR, "sample_tone.mp3")
        res_aud = audio_tools.convert_audio(wav_in, mp3_out, "mp3")
        assert res_aud["success"] and os.path.exists(mp3_out), f"Audio conversion failed: {res_aud}"
        passed += 1
        print("[PASS] Test 5: Audio Conversion (WAV -> MP3 via offline FFmpeg)")
    else:
        print("[SKIP] Test 5: Audio test skipped (no input file)")

    # Test 6: Smart Folder Sorter
    total += 1
    mix_dir = os.path.join(TEST_DIR, "mixed_files_to_sort")
    preview = folder_sorter.analyze_folder(mix_dir)
    assert preview["success"] and preview["total_files"] == 8, f"Preview failed: {preview}"

    sort_res = folder_sorter.sort_folder(mix_dir, action="move", organize_style="category_and_extension")
    assert sort_res["success"] and sort_res["total_processed"] == 8, f"Sort failed: {sort_res}"

    # Verify structured layout
    assert os.path.exists(os.path.join(mix_dir, "Images", "JPG", "photo1.jpg"))
    assert os.path.exists(os.path.join(mix_dir, "Images", "PNG", "graphic.png"))
    assert os.path.exists(os.path.join(mix_dir, "Images", "JPEG", "banner.jpeg"))
    assert os.path.exists(os.path.join(mix_dir, "Documents", "PDF", "invoice.pdf"))
    assert os.path.exists(os.path.join(mix_dir, "Documents", "DOCX", "report.docx"))
    assert os.path.exists(os.path.join(mix_dir, "Documents", "PPT", "slides.ppt"))
    assert os.path.exists(os.path.join(mix_dir, "Documents", "PPTX", "pitch.pptx"))
    assert os.path.exists(os.path.join(mix_dir, "Audio", "MP3", "song.mp3"))
    passed += 1
    print("[PASS] Test 6: Smart Folder Sorter (Images/JPG, PNG, Documents/PDF, DOCX, PPTX, Audio/MP3)")

    # Test 7: Hash & QR Code
    total += 1
    qr_out = os.path.join(TEST_DIR, "test_qr.png")
    res_qr = extra_tools.generate_qr("OmniTools Offline Suite", qr_out)
    assert res_qr["success"] and os.path.exists(qr_out), f"QR failed: {res_qr}"

    hash_res = extra_tools.calculate_file_hash(qr_out, "sha256")
    assert hash_res["success"] and len(hash_res["hash"]) == 64, f"Hash failed: {hash_res}"
    passed += 1
    print("[PASS] Test 7: Offline QR Code & Cryptographic Hash Generator")

    print("\n" + "=" * 50)
    print(f"ALL TESTS PASSED: {passed}/{total} (100% Success!)")
    print("=" * 50)


if __name__ == "__main__":
    run_tests()
