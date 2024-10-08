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

def calculate_stats(transaction_data):
    # Initial calculations with updated column names
    min_date = transaction_data['date'].min()
    max_date = transaction_data['date'].max()
    total_orders = transaction_data['order_id'].nunique()
    total_lines = len(transaction_data)
    total_pieces = transaction_data['quantity'].sum(skipna=True)
    
    # Average calculations
    lines_per_order = total_lines / total_orders
    pieces_per_line = total_pieces / total_lines
    pieces_per_order = total_pieces / total_orders
    
    # Creating a DataFrame to hold results
    result_df = pd.DataFrame({
        'statistic': [
            "Start Date",
            "End Date",
            "Total Orders",
            "Total Lines",
            "Total Pieces",
            "Avg Lines per Order",
            "Avg Pieces per Line",
            "Avg Pieces per Order"
        ],
        'result': [
            min_date.strftime('%Y-%m-%d'),
            max_date.strftime('%Y-%m-%d'),
            f"{total_orders:,}",
            f"{total_lines:,}",
            f"{total_pieces:,.2f}",
            f"{lines_per_order:.2f}",
            f"{pieces_per_line:.2f}",
            f"{pieces_per_order:.2f}"
        ]
    })
    
    return result_df

def create_app(username, static_dir):
    app_ui = ui.page_fluid(
        ui.tags.head(
            ui.tags.link(rel="stylesheet", href="http://127.0.0.1:5000/static/styles.css"),
            ui.tags.link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap"),
            ui.tags.script(src="https://cdn.plot.ly/plotly-2.20.0.min.js"),

            ui.tags.style("""
                .summary-stats-table {
                    width: 100%;
                    border-collapse: collapse;
                    background-color: #ffffff;
                }
                .summary-stats-table th, .summary-stats-table td {
                    text-align: left;
                    padding: 8px;
                    border-bottom: 1px solid #ddd;
                }
                .summary-stats-table th {
                    background-color: #ffffff;
                }
            """)
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
                ui.a("Logout", href="http://127.0.0.1:5000/logout", class_="logout-btn")
            )
        ),
        ui.navset_tab(
            ui.nav_panel("Summary", 
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h3("CHART EDITOR"),
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
                    ui.h2("Summary Statistics"),
                    ui.output_table("summary_stats"),
                    ui.h2("Daily Activity"),
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
            mask = (df['date'] >= start_date) & (df['date'] <= end_date)
            return df[mask]

        @output
        @render.ui
        def summary_stats():
            data = filtered_data()
            stats_df = calculate_stats(data)
            
            ################################ Create a custom HTML table
            table_html = ui.HTML(f"""
                <table class="summary-stats-table">
                    <thead>
                        <tr>
                            <th>Statistic</th>
                            <th>Result</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td>{row['statistic']}</td><td>{row['result']}</td></tr>" for _, row in stats_df.iterrows())}
                    </tbody>
                </table>
            """)
            
            return table_html

        @output
        @render.ui
        def activity_plot():
            data = filtered_data()
            daily_activity = data.groupby('date').agg(
                daily_orders=('order_id', 'nunique'),
                daily_lines=('order_id', 'count'),
                daily_qty=('quantity', 'sum')
            ).reset_index()
            
            metrics = input.metrics()
            if isinstance(metrics, str):
                metrics = [metrics]
            if input.chart_type() == "Line":
                fig = px.line(daily_activity, x='date', y=metrics,
                              labels={'value': 'Count', 'variable': 'Metric'},
                              title='Daily Activity')
            else:
                fig = px.bar(daily_activity, x='date', y=metrics,
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
            data = filtered_data()
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