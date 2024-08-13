from shiny import App, ui, render, reactive
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import sys
from datetime import datetime, time

# Load the data
try:
    df = pd.read_csv('./transaction_data.csv', encoding='utf-8')
    df['date'] = pd.to_datetime(df['date'])
    df['order_id'] = df['order_id'].astype(str)

    print("Data loaded successfully")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Columns in df: {df.columns.tolist()}")

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

    print("Daily activity data prepared successfully")
    print(f"Columns in daily_activity: {daily_activity.columns.tolist()}")
except Exception as e:
    print(f"Error during data preparation: {str(e)}")
    sys.exit(1)

# Define UI
app_ui = ui.page_fluid(
    ui.h1("Elite Ops Dashboard"),
    ui.row(
        ui.column(4,
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
        ui.column(8,
            ui.h2("Daily Activity"),
            ui.output_ui("activity_plot"),
            ui.h2("Top Products"),
            ui.output_ui("top_products_plot"),
        )
    ),
    ui.tags.head(ui.tags.script(src="https://cdn.plot.ly/plotly-latest.min.js")),
)

# Define server logic
def server(input, output, session):
    @reactive.Calc
    def filtered_data():
        start_date = pd.to_datetime(input.start_date()).floor('D')
        end_date = pd.to_datetime(input.end_date()).ceil('D') - pd.Timedelta(seconds=1)
        print(f"Filtering data from {start_date} to {end_date}")
        mask = (daily_activity['date'] >= start_date) & (daily_activity['date'] <= end_date)
        return daily_activity[mask]

    @reactive.Calc
    def filtered_df():
        start_date = pd.to_datetime(input.start_date()).floor('D')
        end_date = pd.to_datetime(input.end_date()).ceil('D') - pd.Timedelta(seconds=1)
        print(f"Filtering df from {start_date} to {end_date}")
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        return df[mask]

    @output
    @render.ui
    def activity_plot():
        data = filtered_data()
        metrics = input.metrics()
        if isinstance(metrics, str):
            metrics = [metrics]
        print(f"Plotting activity data with shape: {data.shape}")
        print(f"Metrics: {metrics}")
        if input.chart_type() == "Line":
            fig = px.line(data, x='date', y=metrics,
                          labels={'value': 'Count', 'variable': 'Metric'},
                          title='Daily Activity')
        else:
            fig = px.bar(data, x='date', y=metrics,
                         labels={'value': 'Count', 'variable': 'Metric'},
                         title='Daily Activity')
        return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False))

    @output
    @render.ui
    def top_products_plot():
        data = filtered_df()
        print(f"Plotting top products with data shape: {data.shape}")
        print(f"Columns in filtered_df: {data.columns.tolist()}")
        if 'sku_id' not in data.columns:
            print("Error: 'sku_id' column not found in the data")
            return ui.p("Error: Product data not available")
        if 'quantity' not in data.columns:
            print("Error: 'quantity' column not found in the data")
            return ui.p("Error: Quantity data not available")
        top_products = data.groupby('sku_id')['quantity'].sum().nlargest(input.top_n()).sort_values(ascending=True)
        fig = px.bar(top_products, orientation='h',
                     labels={'value': 'Total Quantity', 'sku_id': 'Product'},
                     title=f'Top {input.top_n()} Products by Quantity Sold')
        return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False))

# Create and run the app
app = App(app_ui, server)

if __name__ == "__main__":
    print("Starting Shiny app...")
    app.run()

# created by Aaron Cendejas on 8/13/2024