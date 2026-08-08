import streamlit as st


class StreamlitUI:

    def subheader(self, text):
        st.subheader(text)

    def info(self, text):
        st.info(text)

    def success(self, text):
        st.success(text)

    def warning(self, text):
        st.warning(text)

    def write(self, text):
        st.write(text)

    def progress(self, value=0):
        return st.progress(value)


class ConsoleProgress:

    def progress(self, value):
        pass

    def empty(self):
        pass


class ConsoleUI:

    def subheader(self, text):
        print(f"\n{text}")
        print("-" * len(text))

    def info(self, text):
        print(text)

    def success(self, text):
        print(text)

    def warning(self, text):
        print(text)

    def write(self, text):
        print(text)

    def progress(self, value=0):
        return ConsoleProgress()
    