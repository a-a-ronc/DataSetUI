from shiny import App, ui, render, reactive
import pandas as pd
import plotly.express as px

# Load the data
df = pd.read_csv('./transaction_data.csv', encoding='utf-8')
df['date'] = pd.to_datetime(df['date'])
df['order_id'] = df['order_id'].astype(str)

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

# Define your main app UI
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.link(rel="stylesheet", href="/static/styles.css"),
        ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css"),
        ui.tags.script(src="https://cdn.plot.ly/plotly-latest.min.js"),
    ),
    ui.div(
        {"class": "header"},
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
        {"class": "main-content"},
        ui.div(
            {"class": "sidebar"},
            ui.h1("Elite Ops Dashboard"),
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
        ui.div(
            {"class": "chart-area"},
            ui.h2("Daily Activity"),
            ui.output_plot("activity_plot"),
            ui.h2("Top Products"),
            ui.output_plot("top_products_plot"),
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
            ui.a("Visit us on "),
            ui.a(
                ui.tags.i({"class": "fab fa-linkedin linkedin-icon"}),
                href="https://www.linkedin.com/company/build-with-intralog/mycompany/",
                target="_blank"
            )
        )
    ),
)

def server(input, output, session):
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
    @render.plot
    def activity_plot():
        data = filtered_data()
        metrics = input.metrics()
        if isinstance(metrics, str):
            metrics = [metrics]
        if input.chart_type() == "Line":
            fig = px.line(data, x='date', y=metrics,
                          labels={'value': 'Count', 'variable': 'Metric'},
                          title='Daily Activity',
                          color_discrete_sequence=['#0084c6'] * len(metrics))
        else:
            fig = px.bar(data, x='date', y=metrics,
                         labels={'value': 'Count', 'variable': 'Metric'},
                         title='Daily Activity',
                         color_discrete_sequence=['#0084c6'] * len(metrics))
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_color='#333333',
            title_font_color='#333333',
            legend_title_font_color='#333333',
            legend_font_color='#333333',
            xaxis=dict(title_font_color='#333333', tickfont_color='#333333'),
            yaxis=dict(title_font_color='#333333', tickfont_color='#333333')
        )
        return fig

    @output
    @render.plot
    def top_products_plot():
        data = filtered_df()
        if 'sku_id' not in data.columns or 'quantity' not in data.columns:
            return px.scatter()  # Return an empty plot if data is not available
        top_products = data.groupby('sku_id')['quantity'].sum().nlargest(input.top_n()).sort_values(ascending=True)
        fig = px.bar(top_products, orientation='h',
                     labels={'value': 'Total Quantity', 'sku_id': 'Product'},
                     title=f'Top {input.top_n()} Products by Quantity Sold',
                     color_discrete_sequence=['#0084c6'])
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_color='#333333',
            title_font_color='#333333',
            xaxis=dict(title_font_color='#333333', tickfont_color='#333333'),
            yaxis=dict(title_font_color='#333333', tickfont_color='#333333')
        )
        return fig
    