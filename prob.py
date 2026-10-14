import pandas as pd
import time
from csp import CSP, backtracking_search, min_conflicts, forward_checking, mrv, lcv, mac, dom_wdeg

def print_solution_as_table(solution, title): 
    #ξεχωριστός πίνακας για κάθε μέθοδο

    if solution:
        #δημουργώ DataFrame από τη λύση
        df = pd.DataFrame(
            [(lesson, day_period[0], day_period[1]) for lesson, day_period in solution.items()],
            columns=["Μάθημα", "Ημέρα", "Χρονική Περίοδος"]
        )
        
        #ταξινομώ κατά ημέρα και χρονική περίοδο για ομορφιά
        df = df.sort_values(by=["Ημέρα", "Χρονική Περίοδος"]).reset_index(drop=True)
        
        #εκτυπώνω τίτλο
        print(f"\n=== {title} ===")
        
        #εκτυπώνω πίνακα
        print(df.to_string(index=False, justify='left'))
        
        #εκτυπώνω λύση - ελάχιστο αριθμό ημερών
        print(f"\nΕλάχιστος αριθμός ημερών: {len(set(df['Ημέρα']))}")
    else:
        print(f"\n=== {title} ===")
        print("Δεν βρέθηκε λύση.")

def collect_results(method_name, execution_time, checks, min_days):
    #συγκεντρωτικός πίνακας αξιολόγησης
    return {
        "Μέθοδος": method_name,
        "Χρόνος Εκτέλεσης (sec)": round(execution_time, 4),
        #στρογγυλοποιώ σε 4 δεκαδικά
        "Έλεγχοι Περιορισμών": checks,
        "Ελάχιστες Ημέρες": min_days
    }

def main():
    #φορτώνω δεδομένα από το CSV
    try:
        data = pd.read_csv("h3-data.csv", delimiter=",") #χωρισμένα με κόμμα
    except FileNotFoundError:
        print("Το αρχείο h3-data.csv δεν βρέθηκε. Ελέγξτε τη διαδρομή και δοκιμάστε ξανά.")
        return

    #οι μεταωλητές
    variables = list(data['Μάθημα'])

    #τα πεδία τιμών (ημέρες και χρονικές περίοδοι)
    domains = {
        μάθημα: [(day, period) for day in range(1, 22) for period in ["9-12", "12-3", "3-6"]]
        for μάθημα in variables
    }

    #οι γείτονες (περιορισμοί)
    neighbors = {μάθημα: set() for μάθημα in variables}
    #δημιουργώ λεξικό με γείτονες (neighbors) για κάθε μάθημα. 
    #το λεξικό περιέχει ως κλειδί το μάθημα και ως τιμή ένα σύνολο (set) από μαθήματα που έχουν περιορισμούς.
    for i, c1 in data.iterrows():
        for j, c2 in data.iterrows():
            if i != j: #αν τα μαθήματα είναι διαφορετικά
                if c1['Εξάμηνο'] == c2['Εξάμηνο'] or c1['Καθηγητής'] == c2['Καθηγητής']:
                    neighbors[c1['Μάθημα']].add(c2['Μάθημα'])
                    #αν έχουν το ίδιο εξάμηνο ή τον ίδιο καθηγητή, 
                    #προστίθεται το μάθημα c2 ως γείτονας του c1
                if c1['Δύσκολο (TRUE/FALSE)'] and c2['Δύσκολο (TRUE/FALSE)']:
                    neighbors[c1['Μάθημα']].add(c2['Μάθημα'])
                    #αν και τα δύο μαθήματα είναι δύσκολα, 
                    #προστίθεται το μάθημα c2 ως γείτονας του c1
    neighbors = {key: list(value) for key, value in neighbors.items()}
     #μετατρέπω τα σύνολα γειτόνων σε λίστες

    #οι περιορισμοί
    def constraints(A, a, B, b):
        if a == b:
             #αν δύο μαθήματα τοποθετηθούν την ίδια μέρα και ώρα
            return False
        if data[data['Μάθημα'] == A]['Εξάμηνο'].values[0] == data[data['Μάθημα'] == B]['Εξάμηνο'].values[0]:
            if a[0] == b[0]:
                 # Αν δύο μαθήματα είναι στο ίδιο εξάμηνο και τοποθετούνται την ίδια μέρα
                return False
        if data[data['Μάθημα'] == A]['Καθηγητής'].values[0] == data[data['Μάθημα'] == B]['Καθηγητής'].values[0]:
            if a[0] == b[0]:
                # Αν δύο μαθήματα έχουν τον ίδιο καθηγητή και τοποθετούνται την ίδια μέρα
                return False
        if data[data['Μάθημα'] == A]['Δύσκολο (TRUE/FALSE)'].values[0] and data[data['Μάθημα'] == B]['Δύσκολο (TRUE/FALSE)'].values[0]:
            if abs(a[0] - b[0]) < 2:
                # Αν δύο δύσκολα μαθήματα τοποθετηθούν με λιγότερες από 2 μέρες διαφορά
                return False
        return True

    #δημιουργώ το CSP
    exam_csp = CSP(variables, domains, neighbors, constraints)

    #αρχικοποιώ υποστήριξη περικοπής
    exam_csp.support_pruning()

    #λίστα με αποτελέσματα
    results = []

    #λίστα με μεθόδους
    methods = [
        ("Backtracking + Forward Checking + MRV", mrv, forward_checking),
        ("Backtracking + Forward Checking + dom_wdeg", dom_wdeg, forward_checking),
        ("Backtracking + MAC + MRV", mrv, mac),
        ("Backtracking + MAC + dom_wdeg", dom_wdeg, mac),
        ("Min-Conflicts", None, None)
    ]

    for method_name, var_heuristic, inference in methods:
        start_time = time.time()
        if method_name == "Min-Conflicts":
            solution = min_conflicts(exam_csp, max_steps=1000)
        else:
            #οι υπόλοιπες μέθοδοι
            solution = backtracking_search(
                exam_csp,
                select_unassigned_variable=var_heuristic,
                order_domain_values=lcv,
                inference=inference
            )
        execution_time = time.time() - start_time
        checks = exam_csp.nassigns #πλήθος ελέγχων περιορισμών
        min_days = len(set(day for _, (day, _) in solution.items())) if solution else "-"
        #λύση - λιγότερες μέρες
        
        #εκτύπωση της λύσης για την τρέχουσα μέθοδο
        print_solution_as_table(solution, f"Λύση για {method_name}")
        
        #καταγραφή αποτελεσμάτων για τη μέθοδο
        results.append(collect_results(method_name, execution_time, checks, min_days))

    #εκτύπωση συγκεντρωτικού πίνακα αποτελεσμάτων
    results_df = pd.DataFrame(results)
    print("\n=== Συγκεντρωτικός Πίνακας Αποτελεσμάτων ===")
    print(results_df.to_string(index=False, justify='center'))

#κλήση κύριας συνάρτησης
if __name__ == "__main__":
    main()
