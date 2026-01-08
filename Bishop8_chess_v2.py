import sys
import random
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFrame, QScrollArea
)
from PyQt6.QtGui import QFont, QColor, QPainter, QPen
from PyQt6.QtCore import Qt, QRect, QTimer, pyqtSignal

# --- ΝΕΑ CLASS ΓΙΑ ΤΙΣ ΜΙΚΡΟΓΡΑΦΙΕΣ ---
class MiniChessboard(QWidget):
    """
    Ένα μικρό, στατικό widget (160x160) που απλώς ζωγραφίζει
    μια τελική, ασφαλή λύση.
    """
    SQUARE_SIZE = 20 # 20px * 8 = 160px
    
    def __init__(self, solution_set):
        super().__init__()
        
        # Αποθηκεύουμε τη λύση που πρέπει να ζωγραφίσουμε
        self.bishop_positions = solution_set
        
        # Χρώματα (ίδια με την κύρια, αλλά χωρίς γραμμές/απειλές)
        self.colors = [QColor('#F0D9B5'), QColor('#B58863')]
        self.bishop_color = QColor('#007ACC')
        self.bishop_text_color = QColor('#FFFFFF')
        # Μικρότερη γραμματοσειρά για τη μικρογραφία
        self.bishop_font = QFont("Segoe UI Emoji", 12) 
        
        self.setFixedSize(self.SQUARE_SIZE * 8, self.SQUARE_SIZE * 8)

    def paintEvent(self, event):
        """ Ζωγραφίζει μόνο τη σκακιέρα και τους αξιωματικούς. """
        painter = QPainter(self)
        
        # 1. Ζωγραφική Σκακιέρας
        for r in range(8):
            for c in range(8):
                color_index = (r + c) % 2
                painter.fillRect(
                    c * self.SQUARE_SIZE, r * self.SQUARE_SIZE,
                    self.SQUARE_SIZE, self.SQUARE_SIZE,
                    self.colors[color_index]
                )

        # 2. Ζωγραφική Αξιωματικών
        for (br, bc) in self.bishop_positions:
            rect = QRect(
                bc * self.SQUARE_SIZE, br * self.SQUARE_SIZE,
                self.SQUARE_SIZE, self.SQUARE_SIZE
            )
            painter.fillRect(rect, self.bishop_color)
            painter.setFont(self.bishop_font)
            painter.setPen(self.bishop_text_color)
            # Χρησιμοποιούμε "B" αντί για "♝" για να φαίνεται καλύτερα σε μικρό μέγεθος
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "B")
        
        painter.end()


# --- CLASS ΖΩΓΡΑΦΙΚΗΣ (ΚΥΡΙΑ ΣΚΑΚΙΕΡΑ) ---
class ChessboardPainter(QWidget):
    """
    Η κύρια class που κάνει τη ζωγραφική του animation.
    (Με μία νέα προσθήκη: το σήμα 'animation_finished')
    """
    
    # Custom Signal: Στέλνει κείμενο
    stats_updated = pyqtSignal(str)
    # --- ΝΕΟ SIGNAL ---
    # Στέλνει την τελική λύση (ένα set) όταν τελειώσει το animation
    animation_finished = pyqtSignal(set)
    
    SQUARE_SIZE = 80
    
    def __init__(self):
        super().__init__()
        
        self.colors = [QColor('#F0D9B5'), QColor('#B58863')]
        self.bishop_color = QColor('#007ACC')
        self.bishop_text_color = QColor('#FFFFFF')
        self.threat_color = QColor(255, 0, 0, 100)
        self.line_colors = [
            QColor('#FF0000'), QColor('#00FF00'), QColor('#0000FF'), QColor('#FFFF00'),
            QColor('#FF00FF'), QColor('#00FFFF'), QColor('#FFA500'), QColor('#800080')
        ]
        self.bishop_font = QFont("Segoe UI Emoji", 40)
        
        self.setFixedSize(self.SQUARE_SIZE * 8, self.SQUARE_SIZE * 8)
        self.setup_animation()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animation_step)

    def setup_animation(self):
        self.full_solution_list = list(self.create_safe_positions())
        self.full_solution_list.sort(key=lambda pos: pos[1])
        
        self.current_step = 0
        self.placed_bishops = []
        self.threatened_squares = set()
        
        self.stats_updated.emit("Το 'Πρόβλημα των 8 Βασιλισσών' έχει 92 λύσεις. Δείτε μία:")
        self.update()

    def restart_animation(self):
        self.timer.stop()
        self.setup_animation()
        self.timer.start(1500) # 1.5 δευτερόλεπτο
        
    def animation_step(self):
        column = self.current_step // 2
        phase = self.current_step % 2
        
        if column >= 8:
            self.timer.stop()
            self.stats_updated.emit("Η λύση ολοκληρώθηκε! Προσθήκη στο ιστορικό.")
            # --- ΕΚΠΟΜΠΗ ΝΕΟΥ ΣΗΜΑΤΟΣ ---
            # Στέλνουμε τη λύση που μόλις φτιάξαμε
            self.animation_finished.emit(set(self.placed_bishops))
            return

        if phase == 0:
            threats_found_this_step = 0
            for r_test in range(8):
                pos_to_test = (r_test, column)
                if self.is_threatened_by_list(pos_to_test, self.placed_bishops):
                    self.threatened_squares.add(pos_to_test)
                    threats_found_this_step += 1
            
            num_safe = 8 - threats_found_this_step
            self.stats_updated.emit(f"Στήλη {column}: {num_safe} ασφαλείς θέσεις βρέθηκαν.")

        elif phase == 1:
            safe_position = self.full_solution_list[column]
            self.placed_bishops.append(safe_position)
            self.stats_updated.emit(f"Στήλη {column}: Τοποθέτηση αξιωματικού στο {safe_position}")

        self.current_step += 1
        self.update()

    # --- (Οι μέθοδοι is_threatened_by_list, create_safe_positions, paintEvent
    # ---  παραμένουν ακριβώς οι ίδιες με πριν) ---

    def is_threatened_by_list(self, pos, bishop_list):
        (r, c) = pos
        for (br, bc) in bishop_list:
            if abs(r - br) == abs(c - bc):
                return True
        return False

    def create_safe_positions(self):
        def is_safe(positions):
            main_diagonals = set()
            anti_diagonals = set()
            for r, c in positions:
                diff = r - c
                sum_ = r + c
                if diff in main_diagonals or sum_ in anti_diagonals:
                    return False
                main_diagonals.add(diff)
                anti_diagonals.add(sum_)
            return True

        while True:
            positions = set()
            columns = list(range(8))
            random.shuffle(columns)
            for r in range(8):
                c = columns.pop()
                positions.add((r, c))
            if is_safe(positions):
                return positions 

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # ΒΗΜΑ 1: Σκακιέρα
        for r in range(8):
            for c in range(8):
                color_index = (r + c) % 2
                painter.fillRect(
                    c * self.SQUARE_SIZE, r * self.SQUARE_SIZE,
                    self.SQUARE_SIZE, self.SQUARE_SIZE,
                    self.colors[color_index]
                )

        # ΒΗΜΑ 2: "Χαραγμένα" Τετράγωνα
        for (tr, tc) in self.threatened_squares:
            painter.fillRect(
                tc * self.SQUARE_SIZE, tr * self.SQUARE_SIZE,
                self.SQUARE_SIZE, self.SQUARE_SIZE,
                self.threat_color
            )

        # ΒΗΜΑ 3: Τοποθετημένοι Αξιωματικοί
        for (br, bc) in self.placed_bishops:
            rect = QRect(
                bc * self.SQUARE_SIZE, br * self.SQUARE_SIZE,
                self.SQUARE_SIZE, self.SQUARE_SIZE
            )
            painter.fillRect(rect, self.bishop_color)
            painter.setFont(self.bishop_font)
            painter.setPen(self.bishop_text_color)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "♝")

        # ΒΗΜΑ 4: Γραμμές
        for (br, bc) in self.placed_bishops:
            pen = QPen(self.line_colors[bc]) 
            pen.setWidth(3)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            
            start_x = bc * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            start_y = br * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            
            for dr, dc in directions:
                cr, cc = br, bc
                while 0 <= cr + dr <= 7 and 0 <= cc + dc <= 7:
                    cr += dr
                    cc += dc
                end_x = cc * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
                end_y = cr * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
                painter.drawLine(start_x, start_y, end_x, end_y)
        
        painter.end()


# --- ΚΥΡΙΑ ΕΦΑΡΜΟΓΗ (ΜΕΓΑΛΗ ΑΛΛΑΓΗ) ---
class MainApp(QWidget):
    """
    Το ΚΥΡΙΟ παράθυρο. Τώρα έχει 2 στήλες:
    1. Αριστερά: Η κύρια εφαρμογή (Μετρητής, Σκακιέρα, Κουμπί)
    2. Δεξιά: Το "Ιστορικό Λύσεων" (Scroll Area με Μικρογραφίες)
    """
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("8-Queens/Bishops Problem Visualizer with History")
        
        # Αυτή είναι η "Βάση Δεδομένων" μας
        self.solution_history = []
        
        # 1. Δημιουργία Κεντρικής ΟΡΙΖΟΝΤΙΑΣ Διάταξης
        top_level_layout = QHBoxLayout(self)
        
        # --- 2. ΑΡΙΣΤΕΡΗ ΠΛΕΥΡΑ (Η κύρια εφαρμογή) ---
        left_panel_widget = QWidget()
        left_layout = QVBoxLayout(left_panel_widget)
        
        # 2a. Μετρητής
        self.info_label = QLabel("Καλώς ήρθατε!")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.info_label.setFrameShape(QFrame.Shape.StyledPanel)
        self.info_label.setFrameShadow(QFrame.Shadow.Sunken)
        left_layout.addWidget(self.info_label)
        
        # 2b. Widget Ζωγραφικής (Η σκακιέρα μας)
        self.chessboard_widget = ChessboardPainter()
        left_layout.addWidget(self.chessboard_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 2c. Κουμπί Επανεκκίνησης
        self.restart_button = QPushButton("Επανεκκίνηση / Έναρξη")
        self.restart_button.setFont(QFont("Arial", 11))
        left_layout.addWidget(self.restart_button)
        
        # Προσθέτουμε την αριστερή πλευρά στην κύρια διάταξη
        top_level_layout.addWidget(left_panel_widget)
        
        # --- 3. ΔΕΞΙΑ ΠΛΕΥΡΑ (Το "Ιστορικό") ---
        right_panel_widget = QWidget()
        right_layout = QVBoxLayout(right_panel_widget)
        right_panel_widget.setFixedWidth(200) # Σταθερό πλάτος
        
        # 3a. Τίτλος Ιστορικού
        history_title = QLabel("Ιστορικό Λύσεων")
        history_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        history_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(history_title)
        
        # 3b. Περιοχή Scroll για τις Μικρογραφίες
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget() # Το widget που θα περιέχει τις μικρογραφίες
        self.gallery_layout = QVBoxLayout(self.scroll_widget) # Η διάταξη για τις μικρογραφίες
        self.gallery_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True) # Σημαντικό
        
        right_layout.addWidget(self.scroll_area) # Προσθέτουμε το scroll area
        
        # Προσθέτουμε τη δεξιά πλευρά στην κύρια διάταξη
        top_level_layout.addWidget(right_panel_widget)
        
        # --- 4. ΣΥΝΔΕΣΕΙΣ (Connections) ---
        self.restart_button.clicked.connect(self.chessboard_widget.restart_animation)
        self.chessboard_widget.stats_updated.connect(self.info_label.setText)
        
        # --- ΝΕΑ ΣΥΝΔΕΣΗ ---
        # Όταν η σκακιέρα τελειώσει (animation_finished),
        # κάλεσε τη δική μας μέθοδο 'add_solution_to_gallery'
        self.chessboard_widget.animation_finished.connect(self.add_solution_to_gallery)

        # 5. Αυτόματη Έναρξη
        QTimer.singleShot(3000, self.chessboard_widget.restart_animation)

    # --- ΝΕΑ ΜΕΘΟΔΟΣ ---
    def add_solution_to_gallery(self, solution_set):
        """
        Αυτή η μέθοδος καλείται όταν τελειώνει ένα animation.
        Δημιουργεί μια νέα μικρογραφία και την προσθέτει
        στην κορυφή του "Ιστορικού".
        """
        # Αποθηκεύουμε τη λύση (αν και δεν τη χρησιμοποιούμε κάπου αλλού)
        self.solution_history.insert(0, solution_set)
        
        # Δημιουργούμε το νέο widget μικρογραφίας
        mini_board = MiniChessboard(solution_set)
        
        # Το προσθέτουμε στην κορυφή του layout της gallery
        self.gallery_layout.insertWidget(0, mini_board, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # (Προαιρετικό) Περιορίζουμε το ιστορικό στις 5 τελευταίες λύσεις
        if self.gallery_layout.count() > 5:
            # Βρίσκουμε το τελευταίο widget
            item_to_remove = self.gallery_layout.itemAt(5)
            # Το αφαιρούμε
            if item_to_remove:
                widget_to_remove = item_to_remove.widget()
                if widget_to_remove:
                    widget_to_remove.deleteLater() # Σβήσιμο

# --- Εκτέλεση Κώδικα ---
app = QApplication(sys.argv)
window = MainApp()
window.show()
sys.exit(app.exec())