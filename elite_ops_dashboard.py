from shiny import App, ui, render, reactive
import pandas as pd
import plotly.express as px
import plotly.utils
import json
from flask_login import login_required
from pathlib import Path

# Get the current directory
current_dir = Path(__file__).parent

# Load the data
df = pd.read_csv(current_dir / 'transaction_data.csv', encoding='utf-8')
df['date'] = pd.to_datetime(df['date'])
df['order_id'] = df['order_id'].astype(str)

# Load product data
product_df = pd.read_csv(current_dir / 'product_data_revised.csv', encoding='utf-8')

# Prepare daily activity data
shipment_agg = df.groupby('order_id').agg(
    lines=('order_id', 'size'),
    qty=('quantity', 'sum'),
    date=('date', 'max')
).reset_index(drop=True)

daily_activity = shipment_agg.groupby('date').agg(
    daily_orders=('date', 'size'),
    daily_lines=('lines', 'sum'),
    daily_qty=('qty', 'sum')
).reset_index()

def create_app(username, static_dir):
    app_ui = ui.page_fluid(
        ui.tags.head(
            ui.tags.link(rel="stylesheet", href="http://127.0.0.1:5000/static/styles.css"),
            ui.tags.link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap"),
            ui.tags.script(src="https://cdn.plot.ly/plotly-2.20.0.min.js"),
        ),
        ui.div(
            {"class": "header"},
            ui.div(
                {"class": "logo-container"},
                ui.a(
                    ui.img({
                        "src": "https://149909083.v2.pressablecdn.com/wp-content/uploads/2023/02/logo_rbg_primary_color.png",
                        "class": "company-logo",
                        "alt": "Intralog"
                    }),
                    href="https://www.intralog.io",
                    target="_blank"
                )
            ),
            ui.div(
                {"class": "user-info"},
                ui.output_text("user_greeting"),
                ui.a("Logout", href="/logout", class_="logout-btn")
            )
        ),
        ui.navset_tab(
            ui.nav_panel("Summary", 
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h3("Controls"),
                        ui.input_date("start_date", "Start date:", value=df['date'].min().date()),
                        ui.input_date("end_date", "End date:", value=df['date'].max().date()),
                        ui.input_selectize(
                            "metrics",
                            "Select metrics to display:",
                            choices=["daily_orders", "daily_lines", "daily_qty"],
                            selected="daily_orders"
                        ),
                        ui.input_numeric("top_n", "Top N products:", value=10, min=1, max=50),
                        ui.input_select(
                            "chart_type",
                            "Select chart type:",
                            choices=["Line", "Bar"],
                        ),
                    ),
                    ui.output_ui("activity_plot"),
                    ui.h2("Top Products"),
                    ui.output_ui("top_products_plot"),
                )
            ),
            ui.nav_panel("Time", 
                ui.h2("Time Analysis"),
                # Add time-related visualizations here
            ),
            ui.nav_panel("Order Profile", 
                ui.h2("Order Profile Analysis"),
                # Add order profile visualizations here
            ),
            ui.nav_panel("SKU Associations", 
                ui.h2("SKU Association Analysis"),
                # Add SKU association visualizations here
            )
        ),
        ui.div(
            {"class": "footer"},
            ui.p(
                ui.tags.strong("Contact Us: "),
                ui.a("✉️ info@intralog.io", href="mailto:info@intralog.io"),
                " | 📞 (385) 202-6857"
            ),
            ui.p(
                "Visit us on ",
                ui.a(
                    ui.tags.span(class_="linkedin-icon"),
                    "LinkedIn",
                    href="https://www.linkedin.com/company/build-with-intralog/mycompany/",
                    target="_blank"
                )
            )
        )
    )

    def server(input, output, session):
        @output
        @render.text
        def user_greeting():
            return f"Welcome, {username}!"

        @reactive.Calc
        def filtered_data():
            start_date = pd.to_datetime(input.start_date()).floor('D')
            end_date = pd.to_datetime(input.end_date()).ceil('D') - pd.Timedelta(seconds=1)
            mask = (daily_activity['date'] >= start_date) & (daily_activity['date'] <= end_date)
            return daily_activity[mask]

        @reactive.Calc
        def filtered_df():
            start_date = pd.to_datetime(input.start_date()).floor('D')
            end_date = pd.to_datetime(input.end_date()).ceil('D') - pd.Timedelta(seconds=1)
            mask = (df['date'] >= start_date) & (df['date'] <= end_date)
            return df[mask]

        @output
        @render.ui
        def activity_plot():
            data = filtered_data()
            metrics = input.metrics()
            if isinstance(metrics, str):
                metrics = [metrics]
            if input.chart_type() == "Line":
                fig = px.line(data, x='date', y=metrics,
                              labels={'value': 'Count', 'variable': 'Metric'},
                              title='Daily Activity')
            else:
                fig = px.bar(data, x='date', y=metrics,
                             labels={'value': 'Count', 'variable': 'Metric'},
                             title='Daily Activity')
            
            fig.update_layout(template="plotly_white")
            plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            return ui.HTML(f"""
            <div id="activity-plot"></div>
            <script>
                var plotData = {plot_json};
                Plotly.newPlot('activity-plot', plotData.data, plotData.layout);
            </script>
            """)

        @output
        @render.ui
        def top_products_plot():
            data = filtered_df()
            if 'sku_id' not in data.columns or 'quantity' not in data.columns:
                return ui.p("No data available")
            top_products = data.groupby('sku_id')['quantity'].sum().nlargest(input.top_n()).sort_values(ascending=True)
            fig = px.bar(top_products, orientation='h',
                         labels={'value': 'Total Quantity', 'sku_id': 'Product'},
                         title=f'Top {input.top_n()} Products by Quantity Sold')
            
            fig.update_layout(template="plotly_white")
            plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            return ui.HTML(f"""
            <div id="top-products-plot"></div>
            <script>
                var plotData = {plot_json};
                Plotly.newPlot('top-products-plot', plotData.data, plotData.layout);
            </script>
            """)

    app = App(app_ui, server)
    return app

# Wrap the Shiny app with login_required
@login_required
def protected_app(request):
    return create_app(request.user.username)(request)