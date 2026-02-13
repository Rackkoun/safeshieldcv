# file frontend/sscv-desktop-app/widgets/report_incident_widget.py
# @author: Rackkoun
import plotly.graph_objects as go
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QTimer
import json

class SSCVIncidentReportChart(QWebEngineView):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_data = []
        self.y_data = []

        self.fig = go.Figure(
            data=[go.Bar(x=self.x_data, y=self.y_data)],
            layout=go.Layout(
                xaxis=dict(title="Time"),
            yaxis=dict(title="Nbr of Incidences"),
            template="plotly_white",
            margin=dict(l=20, r=20, t=40, b=20),
            )
        )
        self.update_html()

    def update_html(self):
        html = self.fig.to_html(
            include_plotlyjs="cdn",
            full_html=False
        )
        self.setHtml(html)
    
    def update_chart(self, labels, values):
        self.fig.data[0].x = labels
        self.fig.data[0].y = values
        self.update_html()