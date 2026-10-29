int grade;
int calculateGrade(int mark) {
    if (mark >= 1 && mark <= 100) {
        grade = 1;
        return grade;
    } else if (mark >= 101 && mark <= 200) {
        grade = 2;
        return grade;
    } else if (mark >= 201 && mark <= 300) {
        grade = 3;
        return grade;
    } else if (mark >= 301 && mark <= 400) {
        grade = 4;
        return grade;
    }
    return 0;
}