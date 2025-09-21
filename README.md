# PDF Learning App

An interactive web application that allows users to upload PDF educational documents, automatically generate summaries, and create quiz questions at different difficulty levels.

## Features

- 📄 **PDF Upload**: Upload PDF documents up to 16MB
- 📝 **Automatic Summarization**: Generate short, medium, and long summaries
- 🎯 **Quiz Generation**: Create easy, medium, and hard level quiz questions
- 📊 **Statistics Tracking**: Track quiz performance and progress
- 🗄️ **Database Storage**: SQLite database for persistent data storage
- 🎨 **Modern UI**: Clean and responsive user interface

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with Flask-SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript
- **PDF Processing**: PyPDF2
- **Text Analysis**: NLTK, scikit-learn
- **UI Framework**: Custom CSS with Tailwind-like classes

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pdf-learning-app.git
   cd pdf-learning-app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python create_tables.py
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## Usage

1. **Upload PDF**: Drag and drop or select a PDF file
2. **Process**: Click "İşle" to generate summaries and quiz questions
3. **Take Quiz**: Choose difficulty level (Easy/Medium/Hard) and answer questions
4. **View Results**: See your performance and detailed explanations
5. **Track Progress**: View statistics in the library section

## Project Structure

```
pdf-learning-app/
├── app.py                 # Main Flask application
├── create_tables.py       # Database initialization script
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── library.html
│   └── quiz.html
├── static/               # CSS and JavaScript files
└── README.md
```

## Database Schema

- **PDF**: Stores uploaded PDF information and content
- **Summary**: Stores generated summaries (short, medium, long)
- **Quiz**: Stores quiz questions and answers
- **Progress**: Tracks user quiz attempts and performance

## API Endpoints

- `GET /` - Home page
- `POST /upload` - Upload PDF file
- `GET /process/<pdf_id>` - Process PDF and generate content
- `GET /quiz/<pdf_id>` - Quiz page
- `POST /submit_quiz/<pdf_id>` - Submit quiz answers
- `GET /library` - Library page with all PDFs
- `DELETE /delete_pdf/<pdf_id>` - Delete PDF from library
- `GET /api/statistics/<pdf_id>` - Get PDF statistics

## Features in Detail

### Quiz System
- **Easy Level**: Word completion questions (5 questions)
- **Medium Level**: Topic comprehension questions (4 questions)  
- **Hard Level**: Text analysis questions (3 questions)
- **Interactive UI**: Clickable options with visual feedback
- **Results Display**: Detailed explanations for each answer

### Summary Generation
- **Short Summary**: Key points extraction
- **Medium Summary**: Detailed overview
- **Long Summary**: Comprehensive analysis

### Statistics Tracking
- Quiz completion rates
- Correct/incorrect answer tracking
- Performance percentages
- Individual question analysis

## Requirements

- Python 3.7+
- Flask 2.3.3
- PyPDF2 3.0.1
- NLTK 3.8.1
- scikit-learn 1.3.0
- SQLite3

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Screenshots

### Home Page
![Home Page](screenshots/home.png)

### Quiz Interface
![Quiz Interface](screenshots/quiz.png)

### Library View
![Library View](screenshots/library.png)

## Future Enhancements

- [ ] User authentication system
- [ ] Multiple language support
- [ ] Advanced quiz types
- [ ] Progress analytics dashboard
- [ ] PDF annotation features
- [ ] Export functionality for summaries and quizzes

## Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

Made with ❤️ for educational purposes