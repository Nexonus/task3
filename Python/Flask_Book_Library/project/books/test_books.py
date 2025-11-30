import unittest
from project import db, app
from project.books.models import Book

class BookUnitTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
# Valid Book Tests:
    def test_valid_book(self):
        book = Book(name='Example Book', author='Test Author', year_published=1309, book_type='science-fiction')
        db.session.add(book)
        db.session.commit()
        self.assertEqual(book.name, 'Example Book')
        self.assertEqual(book.author, 'Test Author')
        self.assertEqual(book.year_published, 1309)
        self.assertEqual(book.book_type, 'science-fiction')
        self.assertEqual(book.status, 'available')

        retrieved_book = Book.query.filter_by(name='Example Book').first()
        
        self.assertIsNotNone(retrieved_book)

    def test_valid_book_with_status(self):
        book = Book(name='Another Example Book', author='Another Test Author', year_published=2136, book_type='fiction', status="lent")
        db.session.add(book)
        db.session.commit()
        self.assertEqual(book.name, 'Another Example Book')
        self.assertEqual(book.author, 'Another Test Author')
        self.assertEqual(book.year_published, 2136)
        self.assertEqual(book.book_type, 'fiction')
        self.assertEqual(book.status, 'lent')

        retrieved_book = Book.query.filter_by(name='Another Example Book').first()
        
        self.assertIsNotNone(retrieved_book)
# Invalid Book Tests:
    # Duplicate:
    def test_duplicate_name_violation(self):
        book1 = Book(name='Duplicate Book', author='Example Author', year_published=2000, book_type='Fiction')
        book2 = Book(name='Duplicate Book', author='Another Example Author', year_published=2031, book_type='Sci-Fi')
        with self.assertRaises(Exception):
            db.session.add(book1)
            db.session.add(book2)
            db.session.commit() # Integrity Error
        
        db.session.rollback() # Transakcja zostaje cofnieta, po probie dodania ksiazki o tym samym tytule.
        self.assertEqual(Book.query.count(), 1)
    # Null Author
    def test_null_author(self):
        book = Book(name='Book', author=None, year_published=2022, book_type='Thriller')
        db.session.add(book)
        with self.assertRaises(Exception):
            db.session.commit() # Null Value Error
        db.session.rollback()
    # Null Booktype
    def test_null_booktype(self):
        book = Book(name='Book', author='Test', year_published=2022, book_type=None)
        db.session.add(book)
        with self.assertRaises(Exception):
            db.session.commit() 
        db.session.rollback()
    # Null Bookname
    def test_null_name(self):
        book = Book(name=None, author='Test', year_published=2022, book_type='Funny type')
        db.session.add(book)
        with self.assertRaises(Exception):
            db.session.commit() 
        db.session.rollback()
    # Null Publishing Year
    def test_null_year(self):
        book = Book(name='Dziady cz. III', author='Adam Mickiewicz', year_published=None, book_type='Dramat')
        db.session.add(book)
        with self.assertRaises(Exception):
            db.session.commit() 
        db.session.rollback()
    # Delete invalid Book
    def test_delete_invalid(self):
        bookA = Book(name='Example Book', author='Example Author', year_published=2021, book_type='Example Type')
        bookB = Book(name='Hello World', author='C++', year_published=4096, book_type='Another Example Type')
        db.session.add(bookA)
        db.session.commit()
        with self.assertRaises(Exception):
            db.session.delete(bookB)
            db.session.commit()
# SQL and JS Injection tests:

    # SQL:
    def test_sql_injection_attempt(self):
        sql_payload = "Hacker Book'); DROP TABLE books; --"
        book = Book(name=sql_payload, author='Hackerman', year_published=2023, book_type='Cyber-Security')
        db.session.add(book)
        db.session.commit()
        retrieved_book = Book.query.filter_by(author='Hacker').first()

        self.assertIsNotNone(retrieved_book)
        self.assertEqual(retrieved_book.name, sql_payload)
        count = Book.query.count()
        self.assertGreaterEqual(count, 1) # Check if other books haven't been removed here
    # XSS / JS: 
    def test_javascript_injection_xss(self):
        xss_payload = "<script>alert('XSS Attack');</script>"
        book = Book(name="Hacking for Newbies", author=xss_payload, year_published=2025, book_type='Cyber-Security')
        db.session.add(book)
        db.session.commit()
        retrieved_book = Book.query.filter_by(name='Hacking for Newbies').first()
        self.assertEqual(retrieved_book.author, xss_payload)

# Extreme Data Tests:
    # Boundary:
    def test_max_string_length(self):
        limit_str = 'X' * 64 
        
        book = Book(name=limit_str, author=limit_str, year_published=2024, book_type='Test')
        db.session.add(book)
        db.session.commit()
        
        saved_book = Book.query.filter_by(name=limit_str).first()
        self.assertEqual(len(saved_book.name), 64)
        self.assertEqual(len(saved_book.author), 64)
    # Overflow Year:
    def test_extreme_integers(self):
        book_negative = Book(name='Negative Age Book', author='Example Author', year_published=-9000, book_type='History')
        book_zero = Book(name='Zero Age Book', author='Another Example Author', year_published=0, book_type='History')
        book_future = Book(name='Future Book', author='Yet Another Example Author', year_published=2147483647, book_type='Sci-Fi')

        db.session.add_all([book_negative, book_zero, book_future])
        db.session.commit()

        self.assertEqual(Book.query.filter_by(name='Negative Age Book').first().year_published, -9000)
        self.assertEqual(Book.query.filter_by(name='Zero Age Book').first().year_published, 0)
        self.assertEqual(Book.query.filter_by(name='Future Book').first().year_published, 2147483647)
if __name__ == '__main__':
    unittest.main()
