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
PAGE_SIZE = 20


@st.cache_data
def get_paper_data(processed_id):
    return DataRetriever.get_paper_data(processed_id)


def add_group():
    st.session_state.groups.append({})


def remove_group(group_idx):
    del st.session_state.groups[group_idx]


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


def add_group_form(idx, remove=False):
    if remove:
        col_header, col_remove = st.columns([0.8, 0.2])
        col_header.header(f"Group {idx+1}", anchor=False)
        col_remove.button("Remove", key=f"remove_group_{idx}",
                        on_click=remove_group, args=(idx,),
                        use_container_width=True)
    else:
        st.header(f"Group {idx+1}", anchor=False)
    form = st.form(f"group_{idx}_form", border=False)
    form.text_input(label='Enter DOI or Pubmed URL of the paper',
                    key=f'group_{idx}_input')
    form.form_submit_button('Add', on_click=add_paper_to_group,
                            args=(idx, form))



def main():
    # Initialize the state
    if "groups" not in st.session_state:
        st.session_state.groups = [{}, {}]
    if "results" not in st.session_state:
        st.session_state.results = None

    st.set_page_config(page_title='crosscheck')

    st.title("crosscheck", anchor=False)
    st.markdown("Search tool for finding scientific papers that combine several concepts (methods, datasets, theories, etc)")
    with st.expander('**TL;DR:** specify several groups of papers, get all papers that cite at least one from each group'):
        st.markdown("""
            #### Idea
            
            The idea behind **crosscheck** is to find scientific papers that combined several concepts (methods, topics, ideas, etc).
            To describe each concept, one can specify a group of papers that are likely to be cited if the concept is discussed.
            Using a graph-based search, it is possible to find all papers that cite at least one paper from each of the groups 
            (therefore, hopefully combining all the concepts).

            **DISCLAIMER**: of course, this approach won't work perfectly since citations may have different meaning.
            Still, it can be a nice alternative to the text-based search for the described use case.

            #### How to use

            1. Form groups of papers by providing their identifiers in the respective input fields. 

                <ul>
                  <li>
                    Provide one identifier per line
                  </li>
                  <li>
                    The following types of identifiers are currently supported:
                    
                    <ul class="text-secondary">
                      <li><tt>https://pubmed.ncbi.nlm.nih.gov/<strong>PMID</strong>/</tt></li>
                      <li><tt>doi: <strong>DOI</strong></tt></li>
                      <li><tt>https://doi.org/<strong>DOI</strong>/</tt></li>
                    </ul>
                  </li>
                </ul>
              </li>
              <li class="list-group-item">
                Click the 'Submit' button. Button label should change to 'Waiting for response...' while the request is being processed.
              </li>
              <li class="list-group-item">
                Once the search is finished, results will be loaded in the table below. 
                
                <ul>
                  <li>
                    Click on the column names to sort papers according to the title, year or number of citations respectively. The default sort order is decreasing by number of citations.
                  </li>
                  <li>
                    Click on the title of any paper to open it in the new tab.
                  </li>
                </ul>
              </li>
              <li class="list-group-item">
                If it was not possible to find any of the paper provided, a warning will appear above the results. 

                <div role="alert" class="alert alert-warning show mt-3">
                  <strong>Warning!</strong>&nbsp;<span>Failed to find the following paper: <tt>10.20/aaa.30.bbb.40</tt></span>
                </div>
              </li>
              <li class="list-group-item">
                If the search fails for any reason, the error message describing the cause of the problem will appear.

                <div role="alert" class="alert alert-danger show mt-3">
                  <strong>Error!</strong>&nbsp;<span>Group <tt>1</tt> is empty</span>
                </div>
              </li>
        """)
    st.divider()

    for group_id, group_dict in enumerate(st.session_state.groups):
        is_removable = group_id > 1
        add_group_form(group_id, is_removable)
        for paper_id, paper_data in group_dict.items():
            display_paper(paper_data, remove=True, 
                          remove_args=(group_id, paper_id))
        st.divider()

    st.button('Add new group', use_container_width=True, on_click=add_group)
    to_run = st.button('Cross-check!', use_container_width=True, type="primary")

    st.header('Results')
    if to_run:
        with st.spinner('Cross-check in progress...'):
            crosschecked, _ = crosscheck(st.session_state.groups)
            crosschecked_data = DataRetriever.get_papers_batch(crosschecked)
            st.session_state.results = crosschecked_data

    if st.session_state.results is not None:
        col_filter, col_sort, col_page = st.columns(3)
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
        
        # Pagination
        # source: https://medium.com/streamlit/paginating-dataframes-with-streamlit-2da29b080920

        with col_page:
            total_pages = (
                len(crosschecked_df) // PAGE_SIZE +  
                int(len(crosschecked_df) % PAGE_SIZE > 0)
            )
            input_disabled = total_pages == 1
            current_page = st.number_input(
                "Page", value=1, disabled=input_disabled,
                min_value=1, max_value=total_pages, step=1,
            )
            start_idx = (current_page - 1) * PAGE_SIZE
            end_idx = min(len(crosschecked_df), start_idx + PAGE_SIZE)
        
        if total_pages > 1:
            st.markdown(f"Page **{current_page}** of **{total_pages}**, "
                        f"showing papers **{start_idx+1}**-**{end_idx}**")

        for paper_data in crosschecked_df.to_dict('records')[start_idx:end_idx]:
            display_paper(paper_data)
    else:
        st.write("Click the 'Cross-check!' button above to start the search "
                 "and get the results.")
        
    st.write("""
        <style>
            a {
                color: inherit !important;
                font-size: calc(1.275rem + .3vw);
                font-weight: 600;
                line-height: 1.2;
                text-decoration: none;
            }
            hr {
                margin: 0.75rem 0px;
            }
            h2 {
                padding-top: 0rem;
            }
        </style>
    """, unsafe_allow_html=True)

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
    main()