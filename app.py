import openai
from transformers import pipeline
def answer_question_bert(context, question):
    """BERT tabanlı model ile soru-cevap"""
    qa_pipeline = pipeline('question-answering', model='distilbert-base-uncased-distilled-squad')
    result = qa_pipeline({'context': context, 'question': question})
    return result['answer']
import yake
from keybert import KeyBERT
def extract_keywords_yake(text, max_keywords=10):
    """YAKE ile anahtar kelime çıkarma"""
    kw_extractor = yake.KeywordExtractor(lan="en", n=1, top=max_keywords)
    keywords = kw_extractor.extract_keywords(text)
    return [kw[0] for kw in keywords]

def extract_keywords_keybert(text, max_keywords=10):
    """KeyBERT ile anahtar kelime çıkarma"""
    kw_model = KeyBERT()
    keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=max_keywords)
    return [kw[0] for kw in keywords]

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from transformers import pipeline
from werkzeug.utils import secure_filename
import PyPDF2
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
import uuid
import os
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# NLTK verilerini indir
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdf_learning.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# NLTK verilerini indir
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdf_learning.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Veritabanı modelleri

class PDF(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    size = db.Column(db.Integer, nullable=False)
    
    # İlişkiler
    summaries = db.relationship('Summary', backref='pdf', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='pdf', lazy=True, cascade='all, delete-orphan')
    progress = db.relationship('Progress', backref='pdf', lazy=True, cascade='all, delete-orphan')

class Summary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pdf_id = db.Column(db.String(36), db.ForeignKey('pdf.id'), nullable=False)
    short_summary = db.Column(db.Text, nullable=False)
    medium_summary = db.Column(db.Text, nullable=False)
    long_summary = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pdf_id = db.Column(db.String(36), db.ForeignKey('pdf.id'), nullable=False)
    question_id = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(20), nullable=False)  # easy, medium, hard
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)  # JSON string
    correct_answer = db.Column(db.String(255), nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pdf_id = db.Column(db.String(36), db.ForeignKey('pdf.id'), nullable=False)
    completed_quizzes = db.Column(db.Text, nullable=True)  # JSON string
    wrong_answers = db.Column(db.Text, nullable=True)  # JSON string
    last_attempt = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def generate_summary_hf(text):
    """Hugging Face ile metin özeti oluştur (BART tabanlı, chunking ile uzun özet)"""
    from transformers import pipeline
    summarizer = pipeline('summarization', model='facebook/bart-large-cnn')
    # Kısa özet
    short = summarizer(text[:1024], max_length=200, min_length=120, do_sample=False)[0]['summary_text']
    # Orta özet
    medium = summarizer(text[:2048], max_length=400, min_length=250, do_sample=False)[0]['summary_text']
    # Uzun özet için metni güvenli parçalara bölüp birleştir
    chunks = []
    # Kelime bazlı chunking
    words = text.split()
    chunk_size = 400  # Her chunk maksimum 400 kelime
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i+chunk_size]
        chunk = ' '.join(chunk_words)
        if len(chunk_words) > 30:
            try:
                summary_chunk = summarizer(chunk, max_length=200, min_length=80, do_sample=False)[0]['summary_text']
                chunks.append(summary_chunk)
            except Exception as e:
                print(f"Chunk özetlenemedi: {e}")
                continue
    long = '\n'.join(chunks)
    return {
        'short': short,
        'medium': medium,
        'long': long if long else medium
    }


def generate_quiz_questions(text, num_questions=5):
    """Quiz soruları oluştur"""
    try:
        print(f"Generating quiz questions from text length: {len(text)}")
        sentences = sent_tokenize(text)
        print(f"Number of sentences: {len(sentences)}")
        
        if len(sentences) < 1:
            print("Not enough sentences, returning empty questions")
            return {'easy': [], 'medium': [], 'hard': []}
        
        # Kelime frekansı
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalpha() and len(word) > 2]  # 3'ten 2'ye düşürdük
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # En sık kullanılan kelimeler
        common_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:30]
        print(f"Common words found: {len(common_words)}")
        
        questions = {'easy': [], 'medium': [], 'hard': []}
        
        # Kolay sorular (kelime tamamlama) - 5 soru
        easy_count = 0
        for i in range(len(sentences)):
            if easy_count >= 5:
                break
            sentence = sentences[i]
            words_in_sentence = word_tokenize(sentence)
            if len(words_in_sentence) > 3:  # 5'ten 3'e düşürdük
                # Rastgele bir kelimeyi seç
                if len(words_in_sentence) > 4:
                    word_idx = np.random.randint(1, len(words_in_sentence)-1)
                else:
                    word_idx = np.random.randint(0, len(words_in_sentence))
                
                correct_word = words_in_sentence[word_idx]
                
                # Yanlış cevaplar oluştur
                wrong_words = [w for w in common_words[:15] if w[0] != correct_word.lower()]
                wrong_answers = [w[0] for w in wrong_words[:3]]
                
                # Eğer yeterli yanlış cevap yoksa, basit kelimeler ekle
                while len(wrong_answers) < 3:
                    wrong_answers.append(f"word{easy_count + len(wrong_answers)}")
                
                question_text = ' '.join([w if i != word_idx else '_____' for i, w in enumerate(words_in_sentence)])
                # Clean question text for JSON compatibility
                clean_question = question_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()
                
                questions['easy'].append({
                    'id': f'easy_{easy_count}',
                    'question': clean_question,
                    'options': shuffle_array([correct_word] + wrong_answers[:3]),
                    'correct': correct_word,
                    'explanation': f'Correct answer: {correct_word}'
                })
                easy_count += 1
        
        # Orta sorular (anlama) - 4 soru
        medium_count = 0
        for i in range(len(sentences)):
            if medium_count >= 4:
                break
            sentence = sentences[i]
            if len(sentence) > 20:  # 30'dan 20'ye düşürdük
                # Cümle analizi ile daha akıllı cevaplar
                sentence_lower = sentence.lower()
                if any(word in sentence_lower for word in ['technology', 'computer', 'software', 'program', 'teknoloji', 'bilgisayar', 'yazılım', 'program']):
                    correct_answer = 'Technology'
                elif any(word in sentence_lower for word in ['education', 'learning', 'school', 'student', 'eğitim', 'öğrenme', 'okul', 'ders', 'öğrenci']):
                    correct_answer = 'Education'
                elif any(word in sentence_lower for word in ['health', 'medical', 'doctor', 'treatment', 'sağlık', 'hasta', 'doktor', 'tedavi']):
                    correct_answer = 'Health'
                elif any(word in sentence_lower for word in ['economy', 'money', 'financial', 'finance', 'ekonomi', 'para', 'mali', 'finans']):
                    correct_answer = 'Economy'
                else:
                    correct_answer = 'General'
                
                options = ['Technology', 'Education', 'Health', 'Economy', 'General']
                if correct_answer in options:
                    options.remove(correct_answer)
                options = [correct_answer] + options[:3]
                
                # Clean sentence for JSON compatibility
                clean_sentence = sentence.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()
                
                questions['medium'].append({
                    'id': f'medium_{medium_count}',
                    'question': f'What is the main topic discussed in this sentence? {clean_sentence}',
                    'options': shuffle_array(options),
                    'correct': correct_answer,
                    'explanation': f'Sentence analysis: {clean_sentence[:50]}...'
                })
                medium_count += 1
        
        # Zor sorular (analiz) - 3 soru
        hard_count = 0
        
        # En sık geçen kelime sorusu
        if len(common_words) > 0 and hard_count < 3:
            most_common = common_words[0][0]
            options = [w[0] for w in common_words[:4]]
            if len(options) < 4:
                options.extend(['word1', 'word2', 'word3'][:4-len(options)])
            
            questions['hard'].append({
                'id': f'hard_{hard_count}',
                'question': 'What is the most frequently used word in this text?',
                'options': shuffle_array(options),
                'correct': most_common,
                'explanation': f'Most frequent word: {most_common} ({common_words[0][1]} times)'
            })
            hard_count += 1
        
        # Metin uzunluğu sorusu
        if len(sentences) > 1 and hard_count < 3:
            avg_length = round(sum(len(s) for s in sentences) / len(sentences))
            options = [str(avg_length), str(avg_length + 10), str(avg_length - 10), str(avg_length + 20)]
            questions['hard'].append({
                'id': f'hard_{hard_count}',
                'question': 'What is the average length of sentences in this text (in characters)?',
                'options': shuffle_array(options),
                'correct': str(avg_length),
                'explanation': f'Average sentence length: {avg_length} characters'
            })
            hard_count += 1
        
        # Kelime sayısı sorusu
        if hard_count < 3:
            total_words = len(words)
            options = [str(total_words), str(total_words + 50), str(total_words - 50), str(total_words + 100)]
            questions['hard'].append({
                'id': f'hard_{hard_count}',
                'question': 'How many total words are in this text?',
                'options': shuffle_array(options),
                'correct': str(total_words),
                'explanation': f'Total word count: {total_words}'
            })
            hard_count += 1
        
        print(f"Generated questions - Easy: {len(questions['easy'])}, Medium: {len(questions['medium'])}, Hard: {len(questions['hard'])}")
        return questions
    except Exception as e:
        print(f"Error generating quiz questions: {e}")
        import traceback
        traceback.print_exc()
        return {'easy': [], 'medium': [], 'hard': []}

def shuffle_array(arr):
    """Array'i karıştır"""
    import random
    shuffled = arr.copy()
    random.shuffle(shuffled)
    return shuffled

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Dosya seçilmedi'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400
        
        if file and file.filename.lower().endswith('.pdf'):
            # PDF içeriğini oku
            filename = secure_filename(file.filename)
            pdf_id = str(uuid.uuid4())
            
            # PDF'den metin çıkar
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            # Veritabanına kaydet
            pdf = PDF(
                id=pdf_id,
                name=filename,
                content=text,
                size=len(text.encode('utf-8'))
            )
            db.session.add(pdf)
            db.session.commit()
            
            print(f"PDF uploaded successfully: {pdf_id}")
            return jsonify({'pdf_id': pdf_id, 'message': 'Dosya başarıyla yüklendi'})
        else:
            return jsonify({'error': 'Geçersiz dosya formatı'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process/<pdf_id>')
def process_pdf(pdf_id):
    try:
        print(f"Processing PDF: {pdf_id}")
        pdf = db.session.get(PDF, pdf_id)
        if not pdf:
            print(f"PDF not found in database: {pdf_id}")
            return jsonify({'error': 'PDF bulunamadı'}), 404

        # Metin zaten veritabanında saklanmış
        text = pdf.content

        # AI ile özet oluştur
        summary = generate_summary_hf(text)
        summary_obj = Summary(
            pdf_id=pdf_id,
            short_summary=summary['short'],
            medium_summary=summary['medium'],
            long_summary=summary['long']
        )
        db.session.add(summary_obj)

        # Quiz oluştur
        print(f"Text length for quiz generation: {len(text)}")
        quiz_data = generate_quiz_questions(text)
        print(f"Quiz data generated: {quiz_data}")

        quiz_count = 0
        for level, questions in quiz_data.items():
            print(f"Processing {level} level: {len(questions)} questions")
            for question in questions:
                quiz_obj = Quiz(
                    pdf_id=pdf_id,
                    question_id=question['id'],
                    level=level,
                    question=question['question'],
                    options=json.dumps(question['options']),
                    correct_answer=question['correct'],
                    explanation=question.get('explanation', '')
                )
                db.session.add(quiz_obj)
                quiz_count += 1

        print(f"Total quiz questions saved: {quiz_count}")

        # İlerleme kaydet
        progress_obj = Progress(
            pdf_id=pdf_id,
            completed_quizzes=json.dumps([]),
            wrong_answers=json.dumps([])
        )
        db.session.add(progress_obj)

        db.session.commit()

        print(f"PDF processed successfully: {pdf_id}")
        return jsonify({'message': 'PDF başarıyla işlendi'})

    except Exception as e:
        print(f"Error processing PDF: {e}")
        return jsonify({'error': 'PDF işlenirken hata oluştu'}), 500

@app.route('/quiz/<pdf_id>')
def quiz_page(pdf_id):
    try:
        pdf = db.session.get(PDF, pdf_id)
        if not pdf:
            return redirect('/')
        
        # Quiz verilerini al
        quiz_objects = Quiz.query.filter_by(pdf_id=pdf_id).all()
        quiz_data = {'easy': [], 'medium': [], 'hard': []}
        
        for quiz in quiz_objects:
            quiz_data[quiz.level].append({
                'id': quiz.question_id,
                'question': quiz.question,
                'options': json.loads(quiz.options),
                'correct': quiz.correct_answer,
                'explanation': quiz.explanation
            })
        
        # Summary verilerini al
        summary_obj = Summary.query.filter_by(pdf_id=pdf_id).first()
        summary_data = None
        if summary_obj:
            summary_data = {
                'short': summary_obj.short_summary,
                'medium': summary_obj.medium_summary,
                'long': summary_obj.long_summary
            }
        
        return render_template('quiz.html', pdf=pdf, quiz=quiz_data, summary=summary_data, pdf_id=pdf_id)
        
    except Exception as e:
        print(f"Error loading quiz: {e}")
        return redirect('/')

@app.route('/submit_quiz/<pdf_id>', methods=['POST'])
def submit_quiz(pdf_id):
    try:
        data = request.get_json()
        answers = data.get('answers', {})
        level = data.get('level', 'easy')
        
        pdf = db.session.get(PDF, pdf_id)
        if not pdf:
            return jsonify({'error': 'PDF bulunamadı'}), 404
        
        # Quiz verilerini al
        quiz_objects = Quiz.query.filter_by(pdf_id=pdf_id, level=level).all()
        
        if not quiz_objects:
            return jsonify({'error': 'Quiz verisi bulunamadı'}), 404
        
        # Cevapları kontrol et
        results = []
        correct_count = 0
        
        for quiz in quiz_objects:
            user_answer = answers.get(quiz.question_id, '')
            is_correct = user_answer == quiz.correct_answer
            
            if is_correct:
                correct_count += 1
            
            results.append({
                'question_id': quiz.question_id,
                'question': quiz.question,
                'user_answer': user_answer,
                'correct_answer': quiz.correct_answer,
                'is_correct': is_correct,
                'explanation': quiz.explanation
            })
        
        # Sonuçları hesapla
        total_questions = len(quiz_objects)
        percentage = round((correct_count / total_questions) * 100) if total_questions > 0 else 0
        
        # İlerlemeyi güncelle
        progress = Progress.query.filter_by(pdf_id=pdf_id).first()
        if not progress:
            progress = Progress(pdf_id=pdf_id)
            db.session.add(progress)
        
        # Mevcut verileri al
        completed_quizzes = json.loads(progress.completed_quizzes or '[]')
        wrong_answers = json.loads(progress.wrong_answers or '[]')
        
        # Yeni quiz sonucunu ekle
        completed_quizzes.append({
            'date': datetime.utcnow().isoformat(),
            'level': level,
            'score': correct_count,
            'total': total_questions,
            'percentage': percentage
        })
        
        # Yanlış cevapları ekle
        for result in results:
            if not result['is_correct']:
                wrong_answers.append({
                    'question_id': result.get('question_id', ''),
                    'question': result['question'],
                    'user_answer': result['user_answer'],
                    'correct_answer': result['correct_answer'],
                    'level': level,
                    'date': datetime.utcnow().isoformat()
                })
        
        # Veritabanını güncelle
        progress.completed_quizzes = json.dumps(completed_quizzes)
        progress.wrong_answers = json.dumps(wrong_answers)
        progress.last_attempt = datetime.utcnow()
        db.session.commit()
        
        print(f"Quiz progress updated for PDF {pdf_id}: {correct_count}/{total_questions} correct, {len(wrong_answers)} wrong answers")
        
        return jsonify({
            'score': correct_count,
            'total': total_questions,
            'percentage': percentage,
            'results': results
        })
        
    except Exception as e:
        print(f"Error submitting quiz: {e}")
        return jsonify({'error': 'Quiz gönderilirken hata oluştu'}), 500

@app.route('/library')
def library():
    pdfs = PDF.query.order_by(PDF.upload_date.desc()).all()  # Sorgu değişmedi
    return render_template('library.html', pdfs=pdfs)

@app.route('/delete_pdf/<pdf_id>', methods=['DELETE'])
def delete_pdf(pdf_id):
    """PDF'i sil (SQLite veritabanından)"""
    try:
        pdf = db.session.get(PDF, pdf_id)
        if not pdf:
            return jsonify({'error': 'PDF bulunamadı'}), 404
        
        # Veritabanından sil (cascade ile otomatik olarak ilgili kayıtlar da silinir)
        db.session.delete(pdf)
        db.session.commit()
        
        print(f"PDF deleted successfully from database: {pdf_id}")
        return jsonify({'message': 'PDF başarıyla silindi'})
        
    except Exception as e:
        print(f"Error deleting PDF: {e}")
        return jsonify({'error': 'PDF silinirken hata oluştu'}), 500

@app.route('/api/statistics/<pdf_id>')
def get_statistics(pdf_id):
    """PDF istatistiklerini getir"""
    try:
        pdf = db.session.get(PDF, pdf_id)
        if not pdf:
            return jsonify({'error': 'PDF bulunamadı'}), 404
        
        # Quiz sorularını say
        quizzes = Quiz.query.filter_by(pdf_id=pdf_id).all()
        total_questions = len(quizzes)
        
        # Seviye bazında soru sayıları
        easy_questions = len([q for q in quizzes if q.level == 'easy'])
        medium_questions = len([q for q in quizzes if q.level == 'medium'])
        hard_questions = len([q for q in quizzes if q.level == 'hard'])
        
        # Progress bilgilerini al
        progress = Progress.query.filter_by(pdf_id=pdf_id).first()
        
        if progress:
            completed_quizzes_data = json.loads(progress.completed_quizzes or '[]')
            wrong_answers_data = json.loads(progress.wrong_answers or '[]')
            
            # Toplam tamamlanan quiz sayısı
            completed_quizzes = len(completed_quizzes_data)
            
            # Toplam doğru ve yanlış cevap sayıları
            total_correct = sum(quiz.get('score', 0) for quiz in completed_quizzes_data)
            wrong_answers = len(wrong_answers_data)
            
            # Başarı oranını hesapla (tüm quiz'lerin ortalaması)
            if completed_quizzes > 0:
                total_questions_attempted = sum(quiz.get('total', 0) for quiz in completed_quizzes_data)
                success_rate = round((total_correct / total_questions_attempted * 100) if total_questions_attempted > 0 else 0, 1)
            else:
                success_rate = 0
        else:
            completed_quizzes = 0
            total_correct = 0
            wrong_answers = 0
            success_rate = 0
        
        statistics = {
            'total_questions': total_questions,
            'easy_questions': easy_questions,
            'medium_questions': medium_questions,
            'hard_questions': hard_questions,
            'completed_quizzes': completed_quizzes,
            'correct_answers': total_correct,
            'wrong_answers': wrong_answers,
            'success_rate': success_rate
        }
        
        print(f"Statistics loaded for PDF {pdf_id}: {statistics}")
        return jsonify(statistics)
        
    except Exception as e:
        print(f"Error loading statistics: {e}")
        return jsonify({'error': 'İstatistikler yüklenirken hata oluştu'}), 500

@app.route('/download/<pdf_id>/<file_type>')
def download_file(pdf_id, file_type):
    try:
        pdf = db.session.get(PDF, pdf_id)
        if not pdf:
            return jsonify({'error': 'PDF bulunamadı'}), 404
        
        if file_type == 'summary':
            summary = Summary.query.filter_by(pdf_id=pdf_id).first()
            if not summary:
                return jsonify({'error': 'Özet bulunamadı'}), 404
            
            content = f"Kısa Özet:\n{summary.short_summary}\n\n"
            content += f"Orta Özet:\n{summary.medium_summary}\n\n"
            content += f"Uzun Özet:\n{summary.long_summary}"
            
            filename = f"{pdf.name}_ozet.txt"
            
        elif file_type == 'quiz':
            quizzes = Quiz.query.filter_by(pdf_id=pdf_id).all()
            if not quizzes:
                return jsonify({'error': 'Quiz bulunamadı'}), 404
            
            content = f"Quiz Soruları - {pdf.name}\n\n"
            current_level = None
            for quiz in quizzes:
                if quiz.level != current_level:
                    current_level = quiz.level
                    content += f"\n=== {quiz.level.upper()} SEVİYE ===\n\n"
                
                content += f"Soru: {quiz.question}\n"
                options = json.loads(quiz.options)
                for i, option in enumerate(options):
                    content += f"{chr(65+i)}) {option}\n"
                content += f"Doğru Cevap: {quiz.correct_answer}\n"
                if quiz.explanation:
                    content += f"Açıklama: {quiz.explanation}\n"
                content += "\n"
            
            filename = f"{pdf.name}_quiz.txt"
        
        else:
            return jsonify({'error': 'Geçersiz dosya tipi'}), 400
        
        # Dosyayı oluştur ve gönder
        from io import BytesIO
        output = BytesIO()
        output.write(content.encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Veritabanı tablolarını oluştur
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)