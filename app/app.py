import os
import pandas as pd
import streamlit as st

from crosscheck.crosscheck import crosscheck
from crosscheck.preprocess import process_line
from crosscheck.retrieve import DataRetriever, AUTH_HEADER, reformat


APP_DEBUG = os.environ.get('APP_DEBUG', 0)
SORT_MAPPING = {
    'Most cited first': {
        'by': 'citationCount',
        'ascending': False
    },
    'Newest first': {
        'by': 'year',
        'ascending': False
    }, 
    'Oldest first': {
        'by': 'year',
        'ascending': True
    }
}

@st.cache_data
def get_paper_data(processed_id):
    return DataRetriever.get_paper_data(processed_id)


def add_group():
    st.session_state.groups.append({})


def add_paper_to_group(group_idx, form):
    paper_id = st.session_state[f'group_{group_idx}_input']
    if not paper_id:
        form.warning('The input is empty, nothing was added')
        return
    
    print(f'add_paper_to_group: group_idx={group_idx}')
    print(f'add_paper_to_group: state before - {st.session_state.groups}')
    processed_id = process_line(paper_id)
    if processed_id in st.session_state.groups[group_idx]:
        form.info('This paper is already present in the group')
    else:
        paper_data = get_paper_data(processed_id)
        if not paper_data:
            form.error('Could not find paper with the specified ID')
            return
        else:
            st.session_state.groups[group_idx][processed_id] = reformat(paper_data)
    print(f'add_paper_to_group: state after - {st.session_state.groups}')


def remove_paper(group_idx, paper_id):
    print(f'remove_paper: group_idx={group_idx}, paper_id={paper_id}')
    del st.session_state.groups[group_idx][paper_id]


def display_paper(paper_data, remove=False, remove_args=()):
    caption_parts = []
    if paper_data.get('authors', ''):
        caption_parts.append(paper_data['authors'])
    if paper_data.get('year', None) is not None:
        caption_parts.append(str(paper_data['year']))
    if paper_data.get('journal', ''):
        caption_parts.append(paper_data['journal'])
    if paper_data.get('citationCount', None) is not None:
        caption_parts.append(f"{paper_data['citationCount']} citations")
    caption = '&nbsp;&#8226;&nbsp;'.join(caption_parts)

    with st.container(border=True):
        st.write(f'  <a href="{paper_data["url"]}">'
                 f'    {paper_data["title"]}'
                 f'  </a>',
                 unsafe_allow_html=True)
        st.caption(caption)
        if remove:
            st.button('Remove', key=f"remove_{paper_data['paperId']}",
                      on_click=remove_paper, args=remove_args)


def add_group_form(idx):
    st.header(f"Group {idx+1}", anchor=False)
    form = st.form(f"group_{idx}_form", border=False)
    form.text_input(label='Enter DOI or Pubmed URL of the paper',
                    key=f'group_{idx}_input')
    form.form_submit_button('Add', on_click=add_paper_to_group,
                            args=(idx, form))



def main():
    if "groups" not in st.session_state:
        st.session_state.groups = [{}, {}]
    if "results" not in st.session_state:
        st.session_state.results = None

    st.title(":bookmark_tabs: crosscheck", anchor=False)

    for group_id, group_dict in enumerate(st.session_state.groups):
        add_group_form(group_id)
        for paper_id, paper_data in group_dict.items():
            display_paper(paper_data, remove=True, 
                        remove_args=(group_id, paper_id))

    st.button('Add new group', use_container_width=True, on_click=add_group)
    to_run = st.button('Cross-check!', use_container_width=True, type="primary")

    st.header('Results')
    if to_run:
        with st.spinner('Cross-check in progress...'):
            crosschecked, _ = crosscheck(st.session_state.groups)
            crosschecked_data = DataRetriever.get_papers_batch(crosschecked)
            st.session_state.results = crosschecked_data

    if st.session_state.results is not None:
        col_filter, col_sort = st.columns(2)
        with col_filter:
            pattern = st.text_input('Title contains:')

        with col_sort:
            order = st.selectbox(
                'Order',
                SORT_MAPPING.keys()
            )
            sort_params = SORT_MAPPING[order]


        crosschecked_df = pd.DataFrame(st.session_state.results)
        filter_mask = crosschecked_df.title.apply(
            lambda x: pattern.lower() in x.lower()
        )
        crosschecked_df = crosschecked_df[filter_mask]\
            .sort_values(by=sort_params['by'], ascending=sort_params['ascending'])

        st.subheader(f"Found {len(crosschecked_df)} paper{'' if len(crosschecked_df) == 1 else 's'}")
        for paper_data in crosschecked_df.to_dict('records'):
            display_paper(paper_data)
    else:
        st.write("Click the 'Cross-check!' button above to start the search "
                "and get the results.")
        
    st.write("<style>"
            " a { "
            "   color: inherit !important;"
            "   font-size: calc(1.275rem + .3vw);"
            "   font-weight: 600;"
            "   line-height: 1.2;"
            "   text-decoration: none;"
            " }"
            "</style>", 
            unsafe_allow_html=True)

    if APP_DEBUG:
        st.header('Debug info')
        st.write({
            'header': AUTH_HEADER,
            'groups': st.session_state.groups,
            'results': st.session_state.results
        })
        if st.session_state.results is not None:
            st.dataframe(pd.DataFrame(st.session_state.results))


if __name__ == "__main__":
    print(APP_DEBUG)
    main()