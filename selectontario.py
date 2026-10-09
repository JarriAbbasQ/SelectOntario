import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Ontario Universities Admission Evaluator",
    page_icon="🎓",
    layout="wide",
)


# ---------------------------------------------------------
# PROBABILITY EVALUATOR
# ---------------------------------------------------------
def calculate_admission_probability(avg, min_avg_val):
  if min_avg_val is None or str(min_avg_val).strip() in [
      "",
      "nan",
      "None",
      "Information not found",
      "TBD",
  ]:
    return "Information not found"

  try:
    cutoff = float(min_avg_val)
    if avg >= cutoff + 1.5:
      return "High (>70%)"
    elif avg >= cutoff:
      return "Medium (35-65%)"
    elif avg >= cutoff - 3.0:
      return "Low (10-25%)"
    else:
      return "Very Low (<5%)"
  except (ValueError, TypeError):
    return "Information not found"


# ---------------------------------------------------------
# LOAD DATA FROM CSV FILE
# ---------------------------------------------------------
@st.cache_data
def load_program_data():
  script_dir = os.path.dirname(os.path.abspath(__file__))
  csv_path = os.path.join(script_dir, "ontario_universities_programs.csv")

  if not os.path.exists(csv_path):
    st.error(
        f"Error: Missing CSV file at {csv_path}. Please place"
        " ontario_universities_programs.csv in the app folder."
    )
    return []

  df = pd.read_csv(csv_path, encoding="utf-8")

  # Ensure mandatory columns exist
  for col in [
      "university",
      "campus",
      "faculty",
      "name",
      "degree",
      "min_avg",
      "prereqs",
      "tier",
      "description",
  ]:
    if col not in df.columns:
      df[col] = "Information not found"

  programs = []
  for _, row in df.iterrows():
    raw_prereqs = str(row["prereqs"])
    if pd.notna(row["prereqs"]) and raw_prereqs.strip() not in [
        "",
        "nan",
        "Information not found",
        "TBD",
    ]:
      prereqs_list = [p.strip() for p in raw_prereqs.split(",")]
    else:
      prereqs_list = []

    raw_avg = row["min_avg"]
    try:
      parsed_avg = (
          float(raw_avg)
          if pd.notna(raw_avg)
          and str(raw_avg).strip() not in ["Information not found", "TBD"]
          else None
      )
    except ValueError:
      parsed_avg = None

    programs.append({
        "university": (
            str(row.get("university", "University of Toronto")).strip()
        ),
        "campus": str(row.get("campus", "Main")).strip(),
        "faculty": str(row.get("faculty", "General")).strip(),
        "name": str(row.get("name", "Program")).strip(),
        "degree": str(row.get("degree", "Undergraduate Degree")).strip(),
        "min_avg": parsed_avg,
        "min_avg_raw": (
            str(raw_avg) if pd.notna(raw_avg) else "Information not found"
        ),
        "prereqs": prereqs_list,
        "tier": str(row.get("tier", "General Tier")).strip(),
        "description": str(
            row.get("description", "No description provided.")
        ).strip(),
    })
  return programs


ALL_PROGRAMS_DB = load_program_data()


def parse_percentage_input(val_str):
  if not val_str or val_str.strip() == "":
    return 0.0
  try:
    val = float(val_str.strip())
    return val if 0.0 <= val <= 100.0 else 0.0
  except ValueError:
    return 0.0


def calculate_top6_avg(courses_dict):
  valid_marks = [v for v in courses_dict.values() if v > 0]
  if not valid_marks:
    return 0.0
  valid_marks.sort(reverse=True)
  top_6 = valid_marks[:6]
  return sum(top_6) / len(top_6)


def check_prereqs(student_courses, program_prereqs):
  student_keys = set(student_courses.keys())
  missing = [req for req in program_prereqs if req not in student_keys]
  return len(missing) == 0, missing


# ---------------------------------------------------------
# SIDEBAR FILTERS (DYNAMIC & CASCADING)
# ---------------------------------------------------------
st.sidebar.header("📋 Student Profile & Filters")
student_name = st.sidebar.text_input("Student Name", "")
st.sidebar.markdown("---")

all_universities = sorted(list(set(p["university"] for p in ALL_PROGRAMS_DB)))
selected_universities = st.sidebar.multiselect(
    "Filter Universities", options=all_universities, default=all_universities
)

# Dynamically populate campuses based on selected universities
available_campuses = sorted(
    list(
        set(
            p["campus"]
            for p in ALL_PROGRAMS_DB
            if p["university"] in selected_universities
        )
    )
)
selected_campuses = st.sidebar.multiselect(
    "Filter Campuses", options=available_campuses, default=available_campuses
)

# Dynamically populate faculties based on selected campuses & universities
available_faculties = sorted(
    list(
        set(
            p["faculty"]
            for p in ALL_PROGRAMS_DB
            if p["university"] in selected_universities
            and p["campus"] in selected_campuses
        )
    )
)
selected_faculties = st.sidebar.multiselect(
    "Filter Faculties", options=available_faculties, default=available_faculties
)

# ---------------------------------------------------------
# MAIN APP INTERFACE
# ---------------------------------------------------------
st.title("🎓 Ontario Universities Admission Evaluator")
st.markdown(
    "Evaluating eligibility for Ontario undergraduate programs based on Grade"
    " 12 (4U/4M) prerequisites and baseline competitive averages."
)

st.header("📊 Grade 12 (4U/4M) Course Marks Input")
tab_math_sci, tab_humanities, tab_electives = st.tabs(
    ["📐 Math & Sciences", "📖 English & Social Sci", "💻 Business & Tech"]
)

with tab_math_sci:
  c1, c2, c3 = st.columns(3)
  mhf4u = c1.text_input(
      "MHF4U (Advanced Functions)", value="", placeholder="e.g. 92", key="mhf4u"
  )
  mcv4u = c2.text_input(
      "MCV4U (Calculus & Vectors)", value="", placeholder="e.g. 90", key="mcv4u"
  )
  mdm4u = c3.text_input(
      "MDM4U (Data Management)", value="", placeholder="", key="mdm4u"
  )
  sph4u = c1.text_input(
      "SPH4U (Physics)", value="", placeholder="e.g. 88", key="sph4u"
  )
  sch4u = c2.text_input(
      "SCH4U (Chemistry)", value="", placeholder="e.g. 85", key="sch4u"
  )
  sbi4u = c3.text_input(
      "SBI4U (Biology)", value="", placeholder="", key="sbi4u"
  )

with tab_humanities:
  c1, c2, c3 = st.columns(3)
  eng4u = c1.text_input(
      "ENG4U (Grade 12 English)", value="", placeholder="e.g. 90", key="eng4u"
  )
  cia4u = c2.text_input(
      "CIA4U (Economics)", value="", placeholder="", key="cia4u"
  )
  cgw4u = c3.text_input(
      "CGW4U (World Issues)", value="", placeholder="", key="cgw4u"
  )

with tab_electives:
  c1, c2, c3 = st.columns(3)
  bat4m = c1.text_input(
      "BAT4M (Accounting)", value="", placeholder="", key="bat4m"
  )
  ics4u = c2.text_input(
      "ICS4U (Computer Science)", value="", placeholder="", key="ics4u"
  )
  elec1 = c3.text_input(
      "Elective 1 (4U/4M)", value="", placeholder="e.g. 88", key="elec1"
  )

all_raw_courses = {
    "ENG4U": parse_percentage_input(eng4u),
    "MHF4U": parse_percentage_input(mhf4u),
    "MCV4U": parse_percentage_input(mcv4u),
    "MDM4U": parse_percentage_input(mdm4u),
    "SPH4U": parse_percentage_input(sph4u),
    "SCH4U": parse_percentage_input(sch4u),
    "SBI4U": parse_percentage_input(sbi4u),
    "ICS4U": parse_percentage_input(ics4u),
    "CIA4U": parse_percentage_input(cia4u),
    "CGW4U": parse_percentage_input(cgw4u),
    "BAT4M": parse_percentage_input(bat4m),
    "Elective 1": parse_percentage_input(elec1),
}

student_courses = {k: v for k, v in all_raw_courses.items() if v > 0.0}
top6_avg = calculate_top6_avg(student_courses)

st.markdown("---")
st.header("🎯 Program Admission Evaluation Breakdown")

m1, m2, m3 = st.columns(3)
m1.metric("Student Name", student_name if student_name else "Candidate")
m2.metric("Courses Entered", f"{len(student_courses)}")
m3.metric(
    "Calculated Top 6 Average",
    f"{top6_avg:.1f}%" if student_courses else "N/A",
)

if len(student_courses) < 3:
  st.info(
      "💡 Enter marks for at least 3 to 6 Grade 12 (4U/4M) courses above to"
      " calculate admission matches across selected university programs."
  )
else:
  filtered_programs = [
      p
      for p in ALL_PROGRAMS_DB
      if p["university"] in selected_universities
      and p["campus"] in selected_campuses
      and p["faculty"] in selected_faculties
  ]

  target_met = []
  reach_met = []
  missing_prereq_progs = []

  for prog in filtered_programs:
    has_prereqs, missing = check_prereqs(student_courses, prog["prereqs"])
    prob_str = calculate_admission_probability(top6_avg, prog["min_avg"])

    cutoff_num = prog["min_avg"] if prog["min_avg"] is not None else 999.0
    is_target_avg = top6_avg >= cutoff_num
    is_medium_or_high_prob = any(tag in prob_str for tag in ["High", "Medium"])

    if not has_prereqs:
      missing_prereq_progs.append((prog, missing, prob_str))
    elif is_target_avg and is_medium_or_high_prob:
      target_met.append((prog, prob_str))
    else:
      reach_met.append((prog, prob_str))

  # Helper function to render items by university
  def render_grouped_programs(program_tuples, category_type="target"):
    grouped = {}
    for item in program_tuples:
      uni = item[0]["university"]
      if uni not in grouped:
        grouped[uni] = []
      grouped[uni].append(item)

    for uni_name in sorted(grouped.keys()):
      st.markdown(f"#### 🏛️ {uni_name}")
      for item in grouped[uni_name]:
        prog = item[0]
        cutoff_label = (
            f"~{prog['min_avg']:.1f}%"
            if prog["min_avg"] is not None
            else prog["min_avg_raw"]
        )

        if category_type == "target":
          prob = item[1]
          with st.expander(
              f"🟢 **{prog['name']}** [{prog['campus']}] | Probability:"
              f" **{prob}** | Cutoff: {cutoff_label}"
          ):
            st.write(
                f"**Campus:** {prog['campus']} | **Faculty:** {prog['faculty']}"
            )
            st.write(f"**Degree:** {prog['degree']} | **Tier:** {prog['tier']}")
            st.write(
                "**Required Prerequisites:**"
                f" {', '.join(prog['prereqs']) if prog['prereqs'] else 'General Grade 12 Requirements'}"
            )
            st.write(f"**Overview:** {prog['description']}")
            st.success(
                f"✔ **Estimated Offer Probability:** **{prob}**. Top 6 average"
                f" (**{top6_avg:.1f}%**) meets or exceeds the baseline"
                f" threshold (**{cutoff_label}**)."
            )

        elif category_type == "reach":
          prob = item[1]
          gap = (
              (prog["min_avg"] - top6_avg)
              if prog["min_avg"] is not None
              else None
          )
          with st.expander(
              f"🔵 **{prog['name']}** [{prog['campus']}] | Probability:"
              f" **{prob}** | Cutoff: {cutoff_label}"
          ):
            st.write(
                f"**Campus:** {prog['campus']} | **Faculty:** {prog['faculty']}"
            )
            st.write(f"**Degree:** {prog['degree']} | **Tier:** {prog['tier']}")
            st.write(
                "**Required Prerequisites:**"
                f" {', '.join(prog['prereqs']) if prog['prereqs'] else 'General Grade 12 Requirements'}"
            )
            st.write(f"**Overview:** {prog['description']}")
            if gap is not None and gap > 0:
              st.warning(
                  f"⚠️ **Estimated Offer Probability:** **{prob}**. Your average"
                  f" (**{top6_avg:.1f}%**) is **-{gap:.1f}%** below the"
                  f" competitive cutoff (**{cutoff_label}**)."
              )
            else:
              st.warning(
                  f"⚠️ **Estimated Offer Probability:** **{prob}**. Heavy"
                  " emphasis placed on supplemental applications, AIFs, or"
                  " video interviews."
              )

        elif category_type == "missing":
          missing_list = item[1]
          prob = item[2]
          with st.expander(
              f"🔴 **{prog['name']}** [{prog['campus']}] | Missing:"
              f" {', '.join(missing_list)}"
          ):
            st.write(
                f"**Campus:** {prog['campus']} | **Faculty:** {prog['faculty']}"
            )
            st.write(f"**Degree:** {prog['degree']} | **Tier:** {prog['tier']}")
            st.write(f"**Required Prerequisites:** {', '.join(prog['prereqs'])}")
            st.error(
                "❌ **Missing required 4U/4M prerequisites:**"
                f" {', '.join(missing_list)}"
            )
            st.write(
                "If prerequisites are completed, your estimated probability"
                f" based on your current top 6 average ({top6_avg:.1f}%) would"
                f" be **{prob}**."
            )

  # GREEN SECTION
  st.subheader(
      "🟢 Target / Competitive Match Options (Average >= Competitive Cutoff)"
  )
  if target_met:
    render_grouped_programs(target_met, category_type="target")
  else:
    st.write(
        "No programs currently fall into the Target tier for the selected"
        " filters based on current average."
    )

  # BLUE SECTION
  st.subheader(
      "🔵 Reach Options (Average < Competitive Baseline or High Supplemental"
      " Weight)"
  )
  if reach_met:
    render_grouped_programs(reach_met, category_type="reach")
  else:
    st.write("No reach programs flagged.")

  # RED SECTION
  st.subheader("🔴 Missing Mandatory Prerequisite Courses")
  if missing_prereq_progs:
    render_grouped_programs(missing_prereq_progs, category_type="missing")
  else:
    st.write("No programs currently flagged for missing prerequisites.")

# ---------------------------------------------------------
# PROMINENT DISCLAIMER & UNIVERSITY ADMISSIONS POLICY NOTES
# ---------------------------------------------------------
st.markdown("---")

st.warning("""
### ⚠️ IMPORTANT DISCLAIMER & NOTICE
**This application provides estimations for informational and guidance purposes only.** 
* Cutoff averages, prerequisite requirements, and probability calculations are based on historical estimates and public data.
* Meeting or exceeding listed cutoffs **does not guarantee admission**. Universities evaluate candidates holistically, taking into account applicant pool volume, repeat course policies, individual course marks, and supplemental assessments.
* **Student Due Diligence:** Applicants and parents must verify official admission requirements directly on official university websites or the Ontario Universities' Application Centre (OUAC) portal before applying.
""")

st.subheader(
    "📌 Selected Universities Admissions Policy Notes & Supplemental Requirements"
)

if not selected_universities:
  st.info(
      "Select one or more universities in the sidebar to view their respective"
      " admissions policies."
  )
else:
  policy_tabs = st.tabs(selected_universities)

  for idx, uni_name in enumerate(selected_universities):
    with policy_tabs[idx]:
      if uni_name == "University of Toronto":
        st.markdown("""
        #### 🏛️ University of Toronto Admissions Policy Notes & Disclaimers
        * **Engineering Online Student Profile (OSP):** Mandatory for all St. George Engineering applicants. Includes personal response questions and timed video/written components.
        * **Rotman Commerce & Computer Science Supplementals:** Rotman Commerce and St. George CS require mandatory supplemental applications evaluated alongside academic marks.
        * **First-Year POSt System (UTM & UTSC):** Admission to 1st year at UTM and UTSC guarantees entry into the program stream, but progression into 2nd-year Specialist/Major streams requires meeting specific 1st-year course mark thresholds (POSt cutoffs).
        * **Repeat Course Policy:** UofT prefers first-attempt marks for competitive programs like Engineering, CS, and Commerce.
        """)
      elif uni_name == "University of Waterloo":
        st.markdown("""
        #### 🏛️ University of Waterloo Admissions Policy Notes & Disclaimers
        * **Admission Information Form (AIF):** Strongly recommended for all programs and **mandatory** for Engineering, Mathematics, and Computer Science. High AIF scores can significantly increase admission chances.
        * **Online Video Interview:** Required for all Engineering and Software Engineering applicants.
        * **Euclid & Contest Scores:** Strongly encouraged for Mathematics and Computer Science applicants to qualify for competitive consideration and entry scholarships.
        * **Repeated Courses:** Waterloo penalizes repeated courses unless valid extenuating circumstances are documented and approved.
        """)
      elif uni_name == "McMaster University":
        st.markdown("""
        #### 🏛️ McMaster University Admissions Policy Notes & Disclaimers
        * **Bachelor of Health Sciences (BHSc) Supplementary Application:** Heavy weight is placed on the supplementary application. Academic cutoff is 90%+, but final offers are heavily driven by response scores.
        * **Engineering I & iSci Video Assessments:** Mandatory online video/written assessments conducted via Kira Talent for Engineering I and Integrated Science (iSci).
        * **DeGroote Business I:** Evaluates top 6 Grade 12 4U/4M average including required math prerequisites.
        """)
      else:
        st.markdown(f"#### 🏛️ {uni_name} Admissions Notes")
        st.write("Refer to the official university portal for specific program notes.")
