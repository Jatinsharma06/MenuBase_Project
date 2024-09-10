from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/bmi', methods=['GET', 'POST'])
def calculate_bmi():
    bmi = None
    category = None

    if request.method == 'POST':
        try:
            height = float(request.form.get('height'))
            weight = float(request.form.get('weight'))

            # Calculate BMI
            bmi = weight / (height ** 2)

            # Classify the BMI
            if bmi < 18.5:
                category = "Underweight"
            elif 18.5 <= bmi < 24.9:
                category = "Normal weight"
            elif 25 <= bmi < 29.9:
                category = "Overweight"
            else:
                category = "Obesity"

        except (TypeError, ValueError):
            category = "Invalid input. Please enter valid numbers for height and weight."

    return render_template('bmi.html', bmi=bmi, category=category)

if __name__ == '__main__':
    app.run(debug=True)
