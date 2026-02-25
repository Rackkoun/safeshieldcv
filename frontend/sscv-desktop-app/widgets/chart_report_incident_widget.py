# file frontend/sscv-desktop-app/widgets/chart_report_incident_widget.py
# @author: Rackkoun
import plotly.graph_objects as go
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QTimer
import json

class SSCVIncidentReportChart(QWebEngineView):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_dates = []
        self.current_counts = []
        self.fig = go.Figure(
            data=[go.Bar(x=[], y=[], marker_color='#FBBC04')],
            layout=go.Layout(
                title="Daily Incidents",
                xaxis=dict(title="Date", type='category'),
                yaxis=dict(title="Count"),
                template="plotly_white",
                margin=dict(l=20, r=20, t=40, b=20),
                bargap=0.2,
                plot_bgcolor='#2b2b2b',
                paper_bgcolor='#2b2b2b',
                font=dict(color='white')
            )
        )
        self.update_html()
        

    def update_html(self):
        html = self.fig.to_html(include_plotlyjs="cdn", full_html=False)
        self.setHtml(html)
    
    def update_chart(self, stats_data):
        """
        stats_data: list of dicts with keys "date" and "count"
        """
        if not stats_data:
            dates = []
            counts = []
        else:
            dates = [item["date"].split("T")[0] for item in stats_data if "date" in item]
            counts = [item["count"] for item in stats_data if "count" in item]

        # Avoid redraw if data hasn't changed
        if dates == self.current_dates and counts == self.current_counts:
            return

        self.current_dates = dates
        self.current_counts = counts

        self.fig.data[0].x = dates
        self.fig.data[0].y = counts
        self.fig.data[0].marker.color = '#FBBC04'  # reset to default
        self.update_html()
        
    
    def highlight_bar(self, index):
        """Highlight the bar at given index (0-based) with a different color."""
        if not self.current_counts or index < 0 or index >= len(self.current_counts):
            return
        colors = ['#FBBC04'] * len(self.current_counts)
        colors[index] = '#EDB308'  # highlight color
        self.fig.data[0].marker.color = colors
        self.update_html()