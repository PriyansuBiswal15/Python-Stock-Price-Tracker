import tkinter as tk
from tkinter import messagebox
import threading

import yfinance as yf


def fetch_stock_data(ticker: str):
    """
    Fetch basic stock information for the given ticker using yfinance.

    Returns a dictionary with:
        - current_price
        - previous_close
        - day_change
        - percent_change

    Raises ValueError if the ticker is invalid or data is missing.
    """
    ticker = ticker.strip()
    if not ticker:
        raise ValueError("Please enter a ticker symbol.")

    ticker_obj = yf.Ticker(ticker)
    info = ticker_obj.history(period="1d")

    # If no rows are returned, assume invalid ticker or no data
    if info.empty:
        raise ValueError("No data found for this ticker. Please check the symbol.")

    # Get the latest row
    latest = info.iloc[-1]

    current_price = float(latest["Close"])
    previous_close = float(latest.get("Previous Close", latest["Open"]))

    day_change = current_price - previous_close
    percent_change = (day_change / previous_close) * 100 if previous_close else 0.0

    return {
        "current_price": current_price,
        "previous_close": previous_close,
        "day_change": day_change,
        "percent_change": percent_change,
    }


class StockPriceTrackerApp:
    """Tkinter GUI application for tracking stock prices."""

    def __init__(self, root: tk.Tk):
        # Store root window reference
        self.root = root
        self.root.title("Stock Price Tracker")
        self.root.resizable(False, False)

        # Configure main padding
        self.root.configure(padx=20, pady=20)

        # Create main frames
        self._create_input_frame()
        self._create_result_frame()
        self._create_status_bar()

    def _create_input_frame(self):
        """Create the frame with label, entry, and button."""
        input_frame = tk.Frame(self.root)
        input_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        # Label prompting user for ticker
        tk.Label(
            input_frame,
            text="Enter Stock Ticker:",
            font=("Segoe UI", 10),
        ).grid(row=0, column=0, padx=(0, 10))

        # Entry field for ticker symbol
        self.ticker_var = tk.StringVar()
        ticker_entry = tk.Entry(
            input_frame,
            textvariable=self.ticker_var,
            width=20,
            font=("Segoe UI", 10),
        )
        ticker_entry.grid(row=0, column=1, padx=(0, 10))
        ticker_entry.bind("<Return>", lambda event: self.on_get_price())

        # Button to trigger price fetch
        get_price_btn = tk.Button(
            input_frame,
            text="Get Price",
            font=("Segoe UI", 10, "bold"),
            command=self.on_get_price,
        )
        get_price_btn.grid(row=0, column=2)

    def _create_result_frame(self):
        """Create the frame that shows the stock information."""
        self.result_frame = tk.LabelFrame(
            self.root,
            text="Stock Information",
            padx=10,
            pady=10,
            font=("Segoe UI", 10, "bold"),
        )
        self.result_frame.grid(row=1, column=0, sticky="ew")

        # Labels for field names
        tk.Label(self.result_frame, text="Current Price:", anchor="w").grid(
            row=0, column=0, sticky="w", pady=3
        )
        tk.Label(self.result_frame, text="Day Change:", anchor="w").grid(
            row=1, column=0, sticky="w", pady=3
        )
        tk.Label(self.result_frame, text="Percentage Change:", anchor="w").grid(
            row=2, column=0, sticky="w", pady=3
        )
        tk.Label(self.result_frame, text="Previous Close:", anchor="w").grid(
            row=3, column=0, sticky="w", pady=3
        )

        # Dynamic labels where values will be displayed
        self.current_price_var = tk.StringVar(value="-")
        self.day_change_var = tk.StringVar(value="-")
        self.percent_change_var = tk.StringVar(value="-")
        self.previous_close_var = tk.StringVar(value="-")

        tk.Label(
            self.result_frame,
            textvariable=self.current_price_var,
            anchor="w",
            width=20,
        ).grid(row=0, column=1, sticky="w", pady=3)

        tk.Label(
            self.result_frame,
            textvariable=self.day_change_var,
            anchor="w",
            width=20,
        ).grid(row=1, column=1, sticky="w", pady=3)

        tk.Label(
            self.result_frame,
            textvariable=self.percent_change_var,
            anchor="w",
            width=20,
        ).grid(row=2, column=1, sticky="w", pady=3)

        tk.Label(
            self.result_frame,
            textvariable=self.previous_close_var,
            anchor="w",
            width=20,
        ).grid(row=3, column=1, sticky="w", pady=3)

    def _create_status_bar(self):
        """Create a status bar at the bottom of the window."""
        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            bd=1,
            relief=tk.SUNKEN,
            font=("Segoe UI", 9),
        )
        status_label.grid(row=2, column=0, sticky="ew", pady=(15, 0))

    def _clear_results(self):
        """Clear previous result texts."""
        self.current_price_var.set("-")
        self.day_change_var.set("-")
        self.percent_change_var.set("-")
        self.previous_close_var.set("-")

    def on_get_price(self):
        """
        Handle the Get Price button click.

        Starts a background thread so the GUI stays responsive
        while fetching data from the internet.
        """
        ticker = self.ticker_var.get().strip()
        if not ticker:
            messagebox.showwarning("Input Error", "Please enter a stock ticker symbol.")
            return

        # Clear old results and update status
        self._clear_results()
        self.status_var.set("Fetching data...")

        # Use a thread to avoid freezing the UI
        threading.Thread(target=self._fetch_and_update, args=(ticker,), daemon=True).start()

    def _fetch_and_update(self, ticker: str):
        """Background task: fetch stock data and then update the GUI."""
        try:
            data = fetch_stock_data(ticker)

            # Prepare formatted strings with two decimal places
            current_price = f"{data['current_price']:.2f}"
            day_change = f"{data['day_change']:.2f}"
            percent_change = f"{data['percent_change']:.2f}%"
            previous_close = f"{data['previous_close']:.2f}"

            # Determine color for day change and percent change
            color = "green" if data["day_change"] >= 0 else "red"

            # Schedule GUI update on the main thread
            self.root.after(
                0,
                lambda: self._update_gui_values(
                    current_price, day_change, percent_change, previous_close, color
                ),
            )
        except ValueError as ve:
            self.root.after(
                0,
                lambda: self._handle_error(str(ve)),
            )
        except Exception as exc:
            # Generic error for unexpected issues or network errors
            self.root.after(
                0,
                lambda: self._handle_error(
                    "Error fetching data. Please check your internet connection or try again later."
                ),
            )

    def _update_gui_values(
        self,
        current_price: str,
        day_change: str,
        percent_change: str,
        previous_close: str,
        color: str,
    ):
        """Update the result labels with new values."""
        self.current_price_var.set(current_price)
        self.day_change_var.set(day_change)
        self.percent_change_var.set(percent_change)
        self.previous_close_var.set(previous_close)

        # Change the label colors for visual feedback on gain/loss
        # Only day change and percent change change color
        for row in (1, 2):
            for widget in self.result_frame.grid_slaves(row=row, column=1):
                widget.configure(fg=color)

        self.status_var.set("Data fetched successfully.")

    def _handle_error(self, message: str):
        """Show an error message and reset status."""
        self.status_var.set("Ready")
        messagebox.showerror("Error", message)


def main():
    """Entry point to start the Tkinter application."""
    root = tk.Tk()
    app = StockPriceTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

